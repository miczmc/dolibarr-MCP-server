## 🚀 Fonctionnalités

### 📊 Gestion CRM complète (6 fonctions)
- **📞 Contacts** : Recherche et création de contacts
- **🏢 Entreprises** : Gestion complète des tiers (recherche, création)
- **📋 Propositions commerciales** : Consultation et création de devis

### 📅 Gestion # Dolibarr MCP Integration

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Une intégration MCP (Model Context Protocol) pour connecter **Claude AI** à votre **CRM Dolibarr**, permettant la gestion directe de vos données CRM via des conversations naturelles.

## 🚀 Fonctionnalités

### 📊 Gestion CRM de base
- **Contacts** : Recherche, création, modification
- **Entreprises** : Gestion complète des tiers
- **Propositions commerciales** : Consultation et création

### 📅 Gestion d'agenda
- **Événements** : Création, modification, suppression de rendez-vous
- **Planning** : Consultation et gestion de l'agenda
- **Synchronisation** : Avec les contacts et entreprises

### 🎫 Gestion des tickets de support
- **Tickets** : Création, assignation, suivi
- **Messages** : Ajout de réponses et communications
- **Statuts** : Mise à jour des états et priorités

## 📋 Prérequis

- **Python 3.8+**
- **Dolibarr** avec API REST activée
- **Claude Desktop** installé
- **Clé API Dolibarr** configurée

## 🛠️ Installation

### 1. Cloner le repository
```bash
git clone https://github.com/votre-username/dolibarr-mcp-integration.git
cd dolibarr-mcp-integration
```

### 2. Créer un environnement virtuel
```bash
python -m venv dolibarr-mcp-env
source dolibarr-mcp-env/bin/activate  # Linux/Mac
# ou
dolibarr-mcp-env\Scripts\activate     # Windows
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration
```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer avec vos paramètres
nano .env
```

## ⚙️ Configuration

### 1. Configuration Dolibarr
1. Activez le module **API REST** dans Dolibarr
2. Créez un utilisateur API avec les permissions appropriées
3. Générez une clé API

### 2. Configuration du serveur MCP
Éditez le fichier `src/dolibarr_mcp_server.py` :
```python
DOLIBARR_BASE_URL = "https://votre-dolibarr.com/api"
DOLIBARR_API_KEY = "votre_cle_api_ici"
```

### 3. Configuration Claude Desktop
Copiez la configuration dans votre fichier Claude Desktop :

**Windows :** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS :** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux :** `~/.config/Claude/claude_desktop_config.json`

Voir `config/claude_desktop_config.example.json` pour un exemple complet.

## 🎯 Utilisation

Une fois configuré, vous pouvez utiliser Claude pour :

### Exemples de commandes
```
"Trouve tous les contacts de l'entreprise ABC Corp"
"Crée un nouveau contact : Marie Dupont, email: marie@example.com"
"Planifie un rendez-vous avec M. Martin demain à 14h"
"Crée un ticket urgent pour le problème de facturation"
"Montre-moi mes événements d'agenda de la semaine"
"Assigne le ticket 123 à Pierre"
```

## 📚 Documentation

- [Guide d'installation](docs/installation.md)
- [Configuration détaillée](docs/configuration.md)
- [Guide d'utilisation](docs/usage.md)

## 🧪 Tests

```bash
# Test de connexion à l'API
python examples/test_connection.py

# Test du serveur MCP
python src/dolibarr_mcp_server.py --test
```

## 🔒 Sécurité

- ⚠️ **Ne jamais commiter votre clé API**
- Utilisez des variables d'environnement
- Limitez les permissions de l'utilisateur API
- Utilisez HTTPS uniquement

## 🤝 Contribution

Les contributions sont les bienvenues ! Merci de :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📄 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🆘 Support

- **Issues** : [GitHub Issues](https://github.com/miczmc/dolibarr-mcp-integration/issues)
- **Documentation** : [Wiki](https://github.com/miczmc/dolibarr-mcp-integration/wiki)
- **Discussions** : [GitHub Discussions](https://github.com/miczmc/dolibarr-mcp-integration/discussions)

## 🏷️ Versions

- **v1.0.0** : Version initiale avec gestion des contacts, entreprises, agenda et tickets

## 🙏 Remerciements

- **Anthropic** pour Claude et le protocole MCP
- **Dolibarr** pour l'excellente API REST
- La communauté open source

---

⭐ **N'oubliez pas de mettre une étoile si ce projet vous aide !**
