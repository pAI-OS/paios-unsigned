package mobile.common;

import java.util.ArrayList;
import java.util.List;

/**
 * Manager for handling abilities within the mobile app.
 */
public class AbilitiesManager {

    private List<String> abilities;

    public AbilitiesManager() {
        abilities = new ArrayList<>();
    }

    /**
     * Adds a new ability.
     * @param ability The ability to add.
     */
    public void addAbility(String ability) {
        abilities.add(ability);
    }

    /**
     * Configures an existing ability.
     * @param ability The ability to configure.
     */
    public void configureAbility(String ability) {
        // Placeholder for ability configuration logic
    }

    /**
     * Retrieves all abilities.
     * @return A list of abilities.
     */
    public List<String> getAbilities() {
        return abilities;
    }
}
