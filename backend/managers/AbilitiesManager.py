import json
import re
import os
import signal
from common.paths import abilities_dir, abilities_data_dir, apps_dir, default_app_id, venv_subdir
from backend.utils import remove_null_fields
from enum import Enum
from pathlib import Path
from threading import Lock
from backend.dependencies.PythonDependency import PythonDependency
from backend.dependencies.ResourceDependency import ResourceDependency
from backend.dependencies.LinuxDependency import LinuxDependency
from backend.dependencies.ContainerDependency import ContainerDependency

import logging
logger = logging.getLogger(__name__)

class AbilityState(Enum):
    AVAILABLE = "available"
    INSTALLING = "installing"
    INSTALLED = "installed"
    UPGRADING = "upgrading"
    UNINSTALLING = "uninstalling"

class AbilitiesManager:
    _instance = None
    _lock = Lock()
    abilities = []

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(AbilitiesManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):  # Ensure initialization happens only once
            with self._lock:
                if not hasattr(self, '_initialized'):
                    self._load_abilities()
                    self._load_dependency_managers()
                    self._initialized = True

    def _load_dependency_managers(self):
        self._dependency_managers = {
            'python': PythonDependency(),
            'resource': ResourceDependency(),
            'linux': LinuxDependency(),
            'container': ContainerDependency()
        }

    def _load_abilities(self):
        for ability_path in abilities_dir.iterdir():
            if ability_path.is_dir():
                versions_info = self._get_versions_info(ability_path)
                version_to_load = versions_info.get('installed') or versions_info.get('latest')
                if version_to_load:
                    ability_data = self._fetch_ability_from_directory(ability_path, version_to_load)
                    if ability_data:
                        if 'versions' in ability_data:
                            ability_data['versions'].update(versions_info)
                        else:
                            ability_data['versions'] = versions_info
                        self.abilities.append(ability_data)

    def _fetch_ability_from_directory(self, ability_path, version):
        version_dir = ability_path / version
        metadata_file = version_dir / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                return metadata
        return None

    def _get_versions_info(self, ability_path):
        semver_pattern = re.compile(r'^\d+\.\d+\.\d+$')
        versions = []
        installed_version = None

        for version_dir in ability_path.iterdir():
            if version_dir.is_dir() and semver_pattern.match(version_dir.name):
                versions.append(version_dir.name)
            elif version_dir.is_file() and version_dir.name == 'installed':
                with open(version_dir, 'r') as f:
                    installed_version = f.read().strip()

        latest_version = max(versions, key=lambda v: list(map(int, v.split('.'))), default=None)

        versions_info = {
            'available': versions,
            'latest': latest_version,
        }
        if installed_version:
            versions_info['installed'] = installed_version

        return versions_info

    def get_ability(self, id, version=None, refresh=True):
        for ability in self.abilities:
            if ability.get('id') == id and (version is None or ability.get('version') == version):
                if refresh:
                    self._refresh_dependencies(ability)
                # remove_null_fields creates a copy so let's return the original reference
                return ability
        raise ValueError(f"Ability with id {id} not found")

    # get/set/del for dependencies to set state (as we were not able to do so by reference)
    def del_value(self, ability_id, key):
        ability = self.get_ability(ability_id)
        if ability[key]:
            del(ability[key])

    def get_value(self, ability_id, key):
        ability = self.get_ability(ability_id)
        return ability.get(key)

    def set_value(self, ability_id, key, value):
        ability = self.get_ability(ability_id)
        ability[key] = value

    def retrieve_abilities(self, offset=0, limit=100, sort_by=None, sort_order='asc', filters=None, query=None):
        filtered_abilities = self._apply_filters(self.abilities, filters)
        if query:
            filtered_abilities = self._apply_query(filtered_abilities, query)
        sorted_abilities = self._apply_sorting(filtered_abilities, sort_by, sort_order)
        total_count = len(sorted_abilities)
        paginated_abilities = sorted_abilities[offset:offset + limit]

        # Apply remove_null_fields to each ability in the paginated list
        paginated_abilities = [remove_null_fields(ability) for ability in paginated_abilities]

        return paginated_abilities, total_count

    def get_dependency(self, ability_id: str, dependency_id: str):
        ability = self.get_ability(ability_id)
        dependency= next((dep for dep in ability.get('dependencies', []) if dep.get('id') == dependency_id), None)
        if not dependency:
            raise ValueError("Dependency not found")
        return dependency

    def _refresh_dependencies(self, ability, dependency_ids=[]):
        dependencies = ability.get('dependencies', [])
        for dep in dependencies:
            if dep.get('id') in dependency_ids or not dependency_ids:
                dep_type = dep.get('type')
                dm = self._dependency_managers.get(dep_type)
                if dm:
                    dm.refresh_status(ability, dep)
                else:
                    logger.error(f"Dependency manager for type '{dep_type}' not found")

    def _apply_filters(self, abilities, filters):
        if not filters:
            return abilities
        filtered_abilities = []
        for ability in abilities:
            if all(ability.get(key) == value for key, value in filters.items()):
                filtered_abilities.append(ability)
        return filtered_abilities

    def _apply_query(self, abilities, query):
        query = query.lower()
        filtered_abilities = []
        for ability in abilities:
            if query in ability.get('id', '').lower() or query in ability.get('description', '').lower():
                filtered_abilities.append(ability)
        return filtered_abilities

    def _apply_sorting(self, abilities, sort_by, sort_order):
        if not sort_by:
            return abilities
        sorted_abilities = sorted(
            abilities,
            key=lambda x: x.get(sort_by),
            reverse=(sort_order == 'desc')
        )
        return sorted_abilities

    def install_ability(self, id, version=None):
        print(f"Installing ability {id} version {version}")
        ability = self.get_ability(id)

        if version is None:
            version = ability['versions']['latest']

        self._state_transition(id, AbilityState.AVAILABLE, AbilityState.INSTALLING, version)
        try:
            # TODO: Perform the installation process here

            # If successful, set state to installed
            self._state_transition(id, AbilityState.INSTALLING, AbilityState.INSTALLED, version)
            return True
        except Exception as e:
            # Rollback state to available
            self._state_transition(id, AbilityState.INSTALLING, AbilityState.AVAILABLE)
            raise ValueError(f"Installation failed: {e}")

    def upgrade_ability(self, id, version=None):
        print(f"Upgrading ability {id} to version {version}")
        ability = self.get_ability(id)

        old_version = ability['versions']['installed']
        if old_version == version:
            raise ValueError(f"Upgrade failed: Ability {id} is already at version {version}")
        if version is None:
            version = ability['versions']['latest']
        try:
            self._state_transition(id, AbilityState.INSTALLED, AbilityState.UPGRADING, version)
            # TODO: Perform the upgrade process here

            # If successful, set state to installed
            self._state_transition(id, AbilityState.UPGRADING, AbilityState.INSTALLED, version)
            return True
        except Exception as e:
            # Rollback state to previous version
            ability['versions']['installed'] = old_version
            self._state_transition(id, AbilityState.UPGRADING, AbilityState.INSTALLED, rollback=True)
            raise ValueError(f"Upgrade failed: {e}")

    def uninstall_ability(self, id):
        print(f"Uninstalling ability {id}")
        ability = self.get_ability(id)

        self._state_transition(id, AbilityState.INSTALLED, AbilityState.UNINSTALLING)
        try:
            # TODO: Perform the uninstallation process here

            # If successful, set state to available
            self._state_transition(id, AbilityState.UNINSTALLING, AbilityState.AVAILABLE)
            return True
        except Exception as e:
            # Rollback state to installed
            self._state_transition(id, AbilityState.UNINSTALLING, AbilityState.INSTALLED)
            raise ValueError(f"Uninstallation failed: {e}")

    # Simple state machine using lock files to keep track of state for durability    
    def _state_transition(self, id, old_state, new_state, version=None, rollback=False):
        ability = self.get_ability(id)

        def _invalid_state_transition():
            raise ValueError(f"Invalid state transition: {old_state}->{new_state}")

        if old_state == AbilityState.AVAILABLE:  # Not installed
            if new_state == AbilityState.INSTALLING:  # Install in progress
                with open(abilities_dir / id / AbilityState.INSTALLING.value, 'w') as f:
                    f.write(version)
                ability['state'] = AbilityState.INSTALLING.value
            else:
                _invalid_state_transition()
        elif old_state == AbilityState.INSTALLING:
            if new_state == AbilityState.INSTALLED:  # Successful install
                (abilities_dir / id / AbilityState.INSTALLING.value).replace(abilities_dir / id / AbilityState.INSTALLED.value)
                ability['versions']['installed'] = version  # Set the installed version here
                ability['state'] = AbilityState.INSTALLED.value
            elif new_state == AbilityState.AVAILABLE:  # Failed install (no need for rollback to disambiguate)
                (abilities_dir / id / AbilityState.INSTALLING.value).unlink()
                del ability['state']
            else:
                _invalid_state_transition()
        elif old_state == AbilityState.INSTALLED:
            if new_state == AbilityState.UPGRADING:  # Upgrade in progress
                with open(abilities_dir / id / AbilityState.UPGRADING.value, 'w') as f:
                    f.write(version)
                ability['state'] = AbilityState.UPGRADING.value
            elif new_state == AbilityState.UNINSTALLING:  # Uninstall in progress
                (abilities_dir / id / AbilityState.INSTALLED.value).replace(abilities_dir / id / AbilityState.UNINSTALLING.value)
                ability['state'] = AbilityState.UNINSTALLING.value
            else:
                _invalid_state_transition()
        elif old_state == AbilityState.UPGRADING:
            if new_state == AbilityState.INSTALLED:
                ability['state'] = AbilityState.INSTALLED.value
                if not rollback:  # Successful upgrade
                    (abilities_dir / id / AbilityState.UPGRADING.value).replace(abilities_dir / id / AbilityState.INSTALLED.value)
                    ability['versions']['installed'] = version  # Set the installed version here
                else:  # Failed upgrade
                    (abilities_dir / id / AbilityState.UPGRADING.value).unlink()
            else:
                _invalid_state_transition()
        elif old_state == AbilityState.UNINSTALLING:
            if new_state == AbilityState.AVAILABLE:  # Successful uninstall
                (abilities_dir / id / AbilityState.UNINSTALLING.value).unlink()
                if ability.get('versions').get('installed'):
                    del ability['versions']['installed']
                if ability.get('state'):
                    del ability['state']
            elif new_state == AbilityState.INSTALLED:  # Unsuccessful uninstall
                (abilities_dir / id / AbilityState.UNINSTALLING.value).replace(abilities_dir / id / AbilityState.INSTALLED.value)
                ability['state'] = AbilityState.INSTALLED.value
            else:
                _invalid_state_transition()

    def start_ability(self, ability_id, app_id=default_app_id):
        import stat
        import os
        import sys
        import subprocess
        import shlex

        print(f"Starting ability {ability_id} in app {app_id}")
        ability = self.get_ability(ability_id)
        if ability is None:
            return {"error": "Ability not found"}, 404

        start_script = ability.get('scripts', {}).get('start', '')
        if start_script is None:
            return {"error": "Ability start script not set"}, 404

        start_script_parts = shlex.split(start_script)

        if start_script_parts is None:
            return {"error": "Unable to determine start script executable"}, 500

        venv_dir = app_id / venv_subdir
        venv_bin_dir = venv_dir / ('bin' if os.name == "posix" else 'Scripts')
        search_paths = [abilities_dir / ability_id, abilities_data_dir / ability_id, venv_bin_dir]
        script_found = False
        for path in search_paths:
            start_script_candidate = os.path.join(path, start_script_parts[0])
            if os.path.exists(start_script_candidate):
                start_script_cwd = path
                start_script_parts[0] = start_script_candidate
                script_found = True
                break
        if not script_found:
            return {"error": f"Start script {start_script_parts[0]} not found in {search_paths}"}, 404

        if os.name == "posix":
            if not os.access(start_script_parts[0], os.X_OK):
                current_permissions = stat.S_IMODE(os.lstat(start_script_parts[0]).st_mode)
                try:
                    os.chmod(start_script_parts[0], current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                except Exception as e:
                    print(f"Warning: Failed to set execute bit on start script: {e}")

        if start_script_parts[0].endswith('.py'):
            python_executable = str(Path(sys.executable))
            start_script_parts.insert(0, python_executable)

        stdout_file_path = Path(start_script_cwd) / f"{ability_id}_stdout.log"
        stderr_file_path = Path(start_script_cwd) / f"{ability_id}_stderr.log"

        stdout_file = open(stdout_file_path, 'w')
        stderr_file = open(stderr_file_path, 'w')

        process = subprocess.Popen(start_script_parts, cwd=start_script_cwd, shell=False, stdout=stdout_file, stderr=stderr_file, text=True)
        ability['pid'] = process.pid

    def stop_ability(self, id):
        ability = self.get_ability(id)

        if 'pid' in ability:
            os.kill(ability['pid'], signal.SIGTERM)
            del ability['pid']

    async def install_dependency(self, ability_id: str, dependency_id: str):
        ability = self.get_ability(ability_id)
        dependency = self.get_dependency(ability_id, dependency_id)

        dm = self._dependency_managers.get(dependency.get('type'))
        if not dm:
            raise ValueError("Unsupported dependency type")

        await dm.install(ability, dependency, background=True)
        #self._load_abilities()
