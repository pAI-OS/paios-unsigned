import Foundation

class PersonasManager {
    private var personas: [String: Persona] = [:]

    func createPersona(id: String, name: String, description: String) {
        let newPersona = Persona(id: id, name: name, description: description)
        personas[id] = newPersona
    }

    func modifyPersona(id: String, name: String?, description: String?) {
        guard let persona = personas[id] else { return }
        if let name = name {
            persona.name = name
        }
        if let description = description {
            persona.description = description
        }
    }

    func retrievePersona(id: String) -> Persona? {
        return personas[id]
    }

    func retrieveAllPersonas() -> [Persona] {
        return Array(personas.values)
    }
}

class Persona {
    let id: String
    var name: String
    var description: String

    init(id: String, name: String, description: String) {
        self.id = id
        self.name = name
        self.description = description
    }
}
