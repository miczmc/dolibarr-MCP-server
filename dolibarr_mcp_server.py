#!/usr/bin/env python3
"""
Serveur MCP pour intégrer Dolibarr CRM avec Claude
Version complète avec gestion des contacts, entreprises, propositions, agenda et tickets
VERSION CORRIGÉE avec tri approprié des événements
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional
import httpx

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dolibarr-mcp")

# Configuration via variables d'environnement
DOLIBARR_BASE_URL = os.getenv("DOLIBARR_BASE_URL", "")
DOLIBARR_API_KEY = os.getenv("DOLIBARR_API_KEY", "")
DEFAULT_LIMIT = int(os.getenv("DEFAULT_LIMIT", "0"))  # 0 = pas de limite
DEFAULT_SORT_ORDER = os.getenv("DEFAULT_SORT_ORDER", "DESC")  # DESC = plus récent en premier

# Vérification de la configuration
if not DOLIBARR_API_KEY:
    logger.error("ERREUR: DOLIBARR_API_KEY non définie. Définissez cette variable d'environnement.")
    sys.exit(1)

if not DOLIBARR_BASE_URL:
    logger.error("ERREUR: DOLIBARR_BASE_URL non définie.")
    sys.exit(1)

logger.info(f"Configuration chargée - URL: {DOLIBARR_BASE_URL}")
logger.info(f"Clé API: {'*' * (len(DOLIBARR_API_KEY) - 4) + DOLIBARR_API_KEY[-4:] if len(DOLIBARR_API_KEY) > 4 else '***'}")
logger.info(f"Limite par défaut: {DEFAULT_LIMIT if DEFAULT_LIMIT > 0 else 'aucune limite'}")
logger.info(f"Ordre par défaut: {DEFAULT_SORT_ORDER}")

class DolibarrAPI:
    """Client pour l'API Dolibarr - VERSION CORRIGÉE"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "DOLAPIKEY": api_key,
            "Content-Type": "application/json"
        }
    
    def _build_params(self, limit: int = None, sort_order: str = None, search_filters: str = "", sort_field: str = None) -> str:
        """Construit les paramètres d'URL pour les requêtes API - VERSION CORRIGÉE"""
        if limit is None:
            limit = DEFAULT_LIMIT
        if sort_order is None:
            sort_order = DEFAULT_SORT_ORDER
        
        params = []
        
        # Ajouter la limite si > 0
        if limit > 0:
            params.append(f"limit={limit}")
        
        # Ajouter l'ordre de tri - CORRECTION PRINCIPALE
        if sort_order.upper() in ["ASC", "DESC"]:
            params.append(f"sortorder={sort_order.upper()}")
            
            # Spécifier le champ de tri selon le contexte
            if sort_field:
                params.append(f"sortfield={sort_field}")
            else:
                # Champ par défaut pour les événements d'agenda
                params.append(f"sortfield=t.datep")
        
        # Ajouter les filtres de recherche
        if search_filters:
            params.append(f"sqlfilters={search_filters}")
        
        return "?" + "&".join(params) if params else ""

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Any:
        """Effectue une requête HTTP vers l'API Dolibarr"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        logger.debug(f"Requête {method} vers {url}")
        if data:
            logger.debug(f"Données: {json.dumps(data, indent=2)}")
        
        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=self.headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=self.headers)
                else:
                    raise ValueError(f"Méthode HTTP non supportée: {method}")
                
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.error(f"Erreur HTTP {e.response.status_code}: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Erreur lors de la requête: {str(e)}")
                raise
    
    # ===== GESTION DES CONTACTS =====
    async def search_contacts(self, search_term: str = "", limit: int = None, sort_order: str = None) -> List[Dict]:
        """Recherche des contacts dans Dolibarr"""
        search_filters = ""
        if search_term:
            search_filters = f"(t.lastname:like:'%{search_term}%') OR (t.firstname:like:'%{search_term}%') OR (t.email:like:'%{search_term}%')"
        
        params = self._build_params(limit, sort_order, search_filters, "t.lastname")
        return await self._make_request("GET", f"contacts{params}")
    
    async def create_contact(self, contact_data: Dict) -> Dict:
        """Crée un nouveau contact"""
        return await self._make_request("POST", "contacts", contact_data)
    
    # ===== GESTION DES ENTREPRISES =====
    async def get_companies(self, search_term: str = "", limit: int = None, sort_order: str = None) -> List[Dict]:
        """Récupère la liste des entreprises"""
        search_filters = ""
        if search_term:
            search_filters = f"(t.name:like:'%{search_term}%')"
        
        params = self._build_params(limit, sort_order, search_filters, "t.name")
        return await self._make_request("GET", f"thirdparties{params}")
    
    async def create_company(self, company_data: Dict) -> Dict:
        """Crée une nouvelle entreprise"""
        return await self._make_request("POST", "thirdparties", company_data)
    
    # ===== GESTION DES PROPOSITIONS =====
    async def get_proposals(self, limit: int = None, sort_order: str = None) -> List[Dict]:
        """Récupère les propositions commerciales - VERSION CORRIGÉE"""
        if limit is None:
            limit = DEFAULT_LIMIT if DEFAULT_LIMIT > 0 else 10
        if sort_order is None:
            sort_order = DEFAULT_SORT_ORDER
            
        params = self._build_params(limit, sort_order, "", "t.datec")
        return await self._make_request("GET", f"proposals{params}")
    
    async def create_proposal(self, proposal_data: Dict) -> Dict:
        """Crée une nouvelle proposition commerciale"""
        return await self._make_request("POST", "proposals", proposal_data)
    
    # ===== AGENDA EVENTS - VERSION CORRIGÉE =====
    async def get_agenda_events(self, limit: int = None, sort_order: str = None) -> List[Dict]:
        """Récupère les événements d'agenda avec tri correct - VERSION CORRIGÉE"""
        if limit is None:
            limit = DEFAULT_LIMIT if DEFAULT_LIMIT > 0 else 200  # Plus d'événements par défaut
        if sort_order is None:
            sort_order = DEFAULT_SORT_ORDER
            
        params = self._build_params(limit, sort_order, "", "t.datep")
        return await self._make_request("GET", f"agendaevents{params}")
    
    async def create_agenda_event(self, event_data: Dict) -> Dict:
        """Crée un nouvel événement d'agenda"""
        return await self._make_request("POST", "agendaevents", event_data)
    
    async def get_agenda_event(self, event_id: str) -> Dict:
        """Récupère un événement d'agenda spécifique"""
        return await self._make_request("GET", f"agendaevents/{event_id}")
    
    async def update_agenda_event(self, event_id: str, event_data: Dict) -> Dict:
        """Met à jour un événement d'agenda"""
        return await self._make_request("PUT", f"agendaevents/{event_id}", event_data)
    
    async def delete_agenda_event(self, event_id: str) -> Dict:
        """Supprime un événement d'agenda"""
        return await self._make_request("DELETE", f"agendaevents/{event_id}")
    
    # ===== TICKETS - VERSION CORRIGÉE =====
    async def get_tickets(self, limit: int = None, sort_order: str = None) -> List[Dict]:
        """Récupère la liste des tickets avec tri correct - VERSION CORRIGÉE"""
        if limit is None:
            limit = DEFAULT_LIMIT if DEFAULT_LIMIT > 0 else 10
        if sort_order is None:
            sort_order = DEFAULT_SORT_ORDER
            
        params = self._build_params(limit, sort_order, "", "t.datec")
        return await self._make_request("GET", f"tickets{params}")
    
    async def create_ticket(self, ticket_data: Dict) -> Dict:
        """Crée un nouveau ticket"""
        return await self._make_request("POST", "tickets", ticket_data)
    
    async def get_ticket(self, ticket_id: str) -> Dict:
        """Récupère un ticket spécifique"""
        return await self._make_request("GET", f"tickets/{ticket_id}")
    
    async def get_ticket_by_ref(self, ref: str) -> Dict:
        """Récupère un ticket par sa référence"""
        return await self._make_request("GET", f"tickets/ref/{ref}")
    
    async def get_ticket_by_track_id(self, track_id: str) -> Dict:
        """Récupère un ticket par son ID de suivi"""
        return await self._make_request("GET", f"tickets/track_id/{track_id}")
    
    async def update_ticket(self, ticket_id: str, ticket_data: Dict) -> Dict:
        """Met à jour un ticket"""
        return await self._make_request("PUT", f"tickets/{ticket_id}", ticket_data)
    
    async def add_ticket_message(self, message_data: Dict) -> Dict:
        """Ajoute un nouveau message à un ticket existant"""
        return await self._make_request("POST", "tickets/newmessage", message_data)
    
    async def delete_ticket(self, ticket_id: str) -> Dict:
        """Supprime un ticket"""
        return await self._make_request("DELETE", f"tickets/{ticket_id}")

# Import MCP avec gestion d'erreur
try:
    import mcp.server.stdio
    import mcp.types as types
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    MCP_AVAILABLE = True
except ImportError as e:
    logger.error(f"Erreur import MCP: {e}")
    MCP_AVAILABLE = False

if not MCP_AVAILABLE:
    logger.error("MCP non disponible. Installez avec: pip install mcp")
    sys.exit(1)

# Instance de l'API Dolibarr
dolibarr_api = DolibarrAPI(DOLIBARR_BASE_URL, DOLIBARR_API_KEY)

# Serveur MCP
server = Server("dolibarr-mcp")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Liste des outils disponibles pour Claude - VERSION CORRIGÉE"""
    return [
        # ===== GESTION DES CONTACTS =====
        types.Tool(
            name="search_contacts",
            description="Recherche des contacts dans Dolibarr CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Terme de recherche (nom, prénom, email)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": f"Nombre maximum de résultats (0=aucune limite, défaut: {DEFAULT_LIMIT})",
                        "default": DEFAULT_LIMIT
                    },
                    "sort_order": {
                        "type": "string",
                        "enum": ["ASC", "DESC"],
                        "description": f"Ordre de tri (ASC=croissant, DESC=décroissant, défaut: {DEFAULT_SORT_ORDER})",
                        "default": DEFAULT_SORT_ORDER
                    }
                }
            }
        ),
        types.Tool(
            name="create_contact",
            description="Crée un nouveau contact dans Dolibarr",
            inputSchema={
                "type": "object",
                "properties": {
                    "firstname": {"type": "string", "description": "Prénom"},
                    "lastname": {"type": "string", "description": "Nom de famille"},
                    "email": {"type": "string", "description": "Adresse email"},
                    "phone": {"type": "string", "description": "Numéro de téléphone"},
                    "socid": {"type": "integer", "description": "ID de l'entreprise associée"}
                },
                "required": ["lastname"]
            }
        ),
        
        # ===== GESTION DES ENTREPRISES =====
        types.Tool(
            name="get_companies",
            description="Récupère la liste des entreprises dans Dolibarr",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Terme de recherche pour filtrer les entreprises"
                    },
                    "limit": {
                        "type": "integer",
                        "description": f"Nombre maximum de résultats (0=aucune limite, défaut: {DEFAULT_LIMIT})",
                        "default": DEFAULT_LIMIT
                    },
                    "sort_order": {
                        "type": "string",
                        "enum": ["ASC", "DESC"],
                        "description": f"Ordre de tri (ASC=croissant, DESC=décroissant, défaut: {DEFAULT_SORT_ORDER})",
                        "default": DEFAULT_SORT_ORDER
                    }
                }
            }
        ),
        types.Tool(
            name="create_company",
            description="Crée une nouvelle entreprise dans Dolibarr",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Nom de l'entreprise"},
                    "email": {"type": "string", "description": "Email de l'entreprise"},
                    "phone": {"type": "string", "description": "Téléphone"},
                    "address": {"type": "string", "description": "Adresse"},
                    "zip": {"type": "string", "description": "Code postal"},
                    "town": {"type": "string", "description": "Ville"},
                    "country_code": {"type": "string", "description": "Code pays (ex: FR)"}
                },
                "required": ["name"]
            }
        ),
        
        # ===== GESTION DES PROPOSITIONS =====
        types.Tool(
            name="get_proposals",
            description="Récupère les propositions commerciales",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": f"Nombre maximum de résultats (0=aucune limite, défaut: {DEFAULT_LIMIT})",
                        "default": DEFAULT_LIMIT
                    },
                    "sort_order": {
                        "type": "string",
                        "enum": ["ASC", "DESC"],
                        "description": f"Ordre de tri (ASC=croissant, DESC=décroissant, défaut: {DEFAULT_SORT_ORDER})",
                        "default": DEFAULT_SORT_ORDER
                    }
                }
            }
        ),
        types.Tool(
            name="create_proposal",
            description="Crée une nouvelle proposition commerciale",
            inputSchema={
                "type": "object",
                "properties": {
                    "socid": {"type": "integer", "description": "ID de l'entreprise cliente"},
                    "ref": {"type": "string", "description": "Référence de la proposition"},
                    "note_public": {"type": "string", "description": "Note publique"},
                    "note_private": {"type": "string", "description": "Note privée"}
                },
                "required": ["socid"]
            }
        ),
        
        # ===== AGENDA EVENTS - VERSION CORRIGÉE =====
        types.Tool(
            name="get_agenda_events",
            description="Récupère la liste des événements d'agenda avec tri correct",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": f"Nombre maximum de résultats (0=aucune limite, défaut: {DEFAULT_LIMIT})",
                        "default": DEFAULT_LIMIT
                    },
                    "sort_order": {
                        "type": "string",
                        "enum": ["ASC", "DESC"],
                        "description": f"Ordre de tri (ASC=croissant, DESC=décroissant, défaut: {DEFAULT_SORT_ORDER})",
                        "default": DEFAULT_SORT_ORDER
                    }
                }
            }
        ),
        types.Tool(
            name="create_agenda_event",
            description="Crée un nouvel événement d'agenda",
            inputSchema={
                "type": "object",
                "properties": {
                    "label": {"type": "string", "description": "Libellé de l'événement"},
                    "datep": {"type": "string", "description": "Date de début (YYYY-MM-DD HH:MM:SS)"},
                    "datef": {"type": "string", "description": "Date de fin (YYYY-MM-DD HH:MM:SS)"},
                    "type_id": {"type": "integer", "description": "ID du type d'événement"},
                    "fk_soc": {"type": "integer", "description": "ID de l'entreprise associée"},
                    "fk_contact": {"type": "integer", "description": "ID du contact associé"},
                    "note": {"type": "string", "description": "Note/Description"},
                    "location": {"type": "string", "description": "Lieu"},
                    "transparency": {"type": "integer", "description": "Transparence (0=occupé, 1=libre)"},
                    "priority": {"type": "integer", "description": "Priorité (1-5)"}
                },
                "required": ["label", "datep"]
            }
        ),
        types.Tool(
            name="get_agenda_event",
            description="Récupère un événement d'agenda spécifique",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "ID de l'événement"}
                },
                "required": ["event_id"]
            }
        ),
        types.Tool(
            name="update_agenda_event",
            description="Met à jour un événement d'agenda",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "ID de l'événement"},
                    "label": {"type": "string", "description": "Libellé de l'événement"},
                    "datep": {"type": "string", "description": "Date de début (YYYY-MM-DD HH:MM:SS)"},
                    "datef": {"type": "string", "description": "Date de fin (YYYY-MM-DD HH:MM:SS)"},
                    "note": {"type": "string", "description": "Note/Description"},
                    "location": {"type": "string", "description": "Lieu"}
                },
                "required": ["event_id"]
            }
        ),
        types.Tool(
            name="delete_agenda_event",
            description="Supprime un événement d'agenda",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "ID de l'événement"}
                },
                "required": ["event_id"]
            }
        ),
        
        # ===== TICKETS - VERSION CORRIGÉE =====
        types.Tool(
            name="get_tickets",
            description="Récupère la liste des tickets de support avec tri correct",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": f"Nombre maximum de résultats (0=aucune limite, défaut: {DEFAULT_LIMIT})",
                        "default": DEFAULT_LIMIT
                    },
                    "sort_order": {
                        "type": "string",
                        "enum": ["ASC", "DESC"],
                        "description": f"Ordre de tri (ASC=croissant, DESC=décroissant, défaut: {DEFAULT_SORT_ORDER})",
                        "default": DEFAULT_SORT_ORDER
                    }
                }
            }
        ),
        types.Tool(
            name="create_ticket",
            description="Crée un nouveau ticket de support",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "Sujet du ticket"},
                    "message": {"type": "string", "description": "Message/Description du problème"},
                    "fk_soc": {"type": "integer", "description": "ID de l'entreprise"},
                    "fk_user_create": {"type": "integer", "description": "ID de l'utilisateur créateur"},
                    "fk_user_assign": {"type": "integer", "description": "ID de l'utilisateur assigné"},
                    "type_code": {"type": "string", "description": "Code du type de ticket"},
                    "category_code": {"type": "string", "description": "Code de la catégorie"},
                    "severity_code": {"type": "string", "description": "Code de sévérité"},
                    "email_from": {"type": "string", "description": "Email de l'expéditeur"},
                    "priority": {"type": "integer", "description": "Priorité (0-5)"}
                },
                "required": ["subject", "message"]
            }
        ),
        types.Tool(
            name="get_ticket",
            description="Récupère un ticket spécifique par ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "ID du ticket"}
                },
                "required": ["ticket_id"]
            }
        ),
        types.Tool(
            name="get_ticket_by_ref",
            description="Récupère un ticket par sa référence",
            inputSchema={
                "type": "object",
                "properties": {
                    "ref": {"type": "string", "description": "Référence du ticket"}
                },
                "required": ["ref"]
            }
        ),
        types.Tool(
            name="get_ticket_by_track_id",
            description="Récupère un ticket par son ID de suivi",
            inputSchema={
                "type": "object",
                "properties": {
                    "track_id": {"type": "string", "description": "ID de suivi du ticket"}
                },
                "required": ["track_id"]
            }
        ),
        types.Tool(
            name="update_ticket",
            description="Met à jour un ticket",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "ID du ticket"},
                    "subject": {"type": "string", "description": "Nouveau sujet"},
                    "fk_user_assign": {"type": "integer", "description": "Nouvel utilisateur assigné"},
                    "priority": {"type": "integer", "description": "Nouvelle priorité"},
                    "progress": {"type": "integer", "description": "Pourcentage de progression (0-100)"},
                    "fk_statut": {"type": "integer", "description": "Nouveau statut"}
                },
                "required": ["ticket_id"]
            }
        ),
        types.Tool(
            name="add_ticket_message",
            description="Ajoute un message à un ticket existant",
            inputSchema={
                "type": "object",
                "properties": {
                    "track_id": {"type": "string", "description": "ID de suivi du ticket"},
                    "message": {"type": "string", "description": "Contenu du message"},
                    "email": {"type": "string", "description": "Email de l'expéditeur"},
                    "private": {"type": "integer", "description": "Message privé (0=public, 1=privé)"}
                },
                "required": ["track_id", "message"]
            }
        ),
        types.Tool(
            name="delete_ticket",
            description="Supprime un ticket",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "ID du ticket"}
                },
                "required": ["ticket_id"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Gestionnaire des appels d'outils - VERSION CORRIGÉE"""
    try:
        # ===== GESTION DES CONTACTS =====
        if name == "search_contacts":
            search_term = arguments.get("search_term", "")
            limit = arguments.get("limit", DEFAULT_LIMIT)
            sort_order = arguments.get("sort_order", DEFAULT_SORT_ORDER)
            results = await dolibarr_api.search_contacts(search_term, limit, sort_order)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(results, indent=2, ensure_ascii=False)
            )]
        
        elif name == "create_contact":
            result = await dolibarr_api.create_contact(arguments)
            return [types.TextContent(
                type="text",
                text=f"Contact créé avec succès. ID: {result.get('id', 'N/A')}"
            )]
        
        # ===== GESTION DES ENTREPRISES =====
        elif name == "get_companies":
            search_term = arguments.get("search_term", "")
            limit = arguments.get("limit", DEFAULT_LIMIT)
            sort_order = arguments.get("sort_order", DEFAULT_SORT_ORDER)
            results = await dolibarr_api.get_companies(search_term, limit, sort_order)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(results, indent=2, ensure_ascii=False)
            )]
        
        elif name == "create_company":
            result = await dolibarr_api.create_company(arguments)
            return [types.TextContent(
                type="text",
                text=f"Entreprise créée avec succès. ID: {result.get('id', 'N/A')}"
            )]
        
        # ===== GESTION DES PROPOSITIONS =====
        elif name == "get_proposals":
            limit = arguments.get("limit", DEFAULT_LIMIT)
            sort_order = arguments.get("sort_order", DEFAULT_SORT_ORDER)
            results = await dolibarr_api.get_proposals(limit, sort_order)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(results, indent=2, ensure_ascii=False)
            )]
        
        elif name == "create_proposal":
            result = await dolibarr_api.create_proposal(arguments)
            return [types.TextContent(
                type="text",
                text=f"Proposition créée avec succès. ID: {result.get('id', 'N/A')}"
            )]
        
        # ===== AGENDA EVENTS - VERSION CORRIGÉE =====
        elif name == "get_agenda_events":
            limit = arguments.get("limit", DEFAULT_LIMIT)
            sort_order = arguments.get("sort_order", DEFAULT_SORT_ORDER)
            results = await dolibarr_api.get_agenda_events(limit, sort_order)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(results, indent=2, ensure_ascii=False)
            )]
        
        elif name == "create_agenda_event":
            result = await dolibarr_api.create_agenda_event(arguments)
            return [types.TextContent(
                type="text",
                text=f"Événement d'agenda créé avec succès. ID: {result.get('id', 'N/A')}"
            )]
        
        elif name == "get_agenda_event":
            event_id = arguments.get("event_id")
            result = await dolibarr_api.get_agenda_event(event_id)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
        
        elif name == "update_agenda_event":
            event_id = arguments.pop("event_id")
            result = await dolibarr_api.update_agenda_event(event_id, arguments)
            return [types.TextContent(
                type="text",
                text=f"Événement d'agenda mis à jour avec succès. ID: {event_id}"
            )]
        
        elif name == "delete_agenda_event":
            event_id = arguments.get("event_id")
            result = await dolibarr_api.delete_agenda_event(event_id)
            return [types.TextContent(
                type="text",
                text=f"Événement d'agenda supprimé avec succès. ID: {event_id}"
            )]
        
        # ===== TICKETS - VERSION CORRIGÉE =====
        elif name == "get_tickets":
            limit = arguments.get("limit", DEFAULT_LIMIT)
            sort_order = arguments.get("sort_order", DEFAULT_SORT_ORDER)
            results = await dolibarr_api.get_tickets(limit, sort_order)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(results, indent=2, ensure_ascii=False)
            )]
        
        elif name == "create_ticket":
            result = await dolibarr_api.create_ticket(arguments)
            return [types.TextContent(
                type="text",
                text=f"Ticket créé avec succès. ID: {result.get('id', 'N/A')}, Référence: {result.get('ref', 'N/A')}, Track ID: {result.get('track_id', 'N/A')}"
            )]
        
        elif name == "get_ticket":
            ticket_id = arguments.get("ticket_id")
            result = await dolibarr_api.get_ticket(ticket_id)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
        
        elif name == "get_ticket_by_ref":
            ref = arguments.get("ref")
            result = await dolibarr_api.get_ticket_by_ref(ref)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
        
        elif name == "get_ticket_by_track_id":
            track_id = arguments.get("track_id")
            result = await dolibarr_api.get_ticket_by_track_id(track_id)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
        
        elif name == "update_ticket":
            ticket_id = arguments.pop("ticket_id")
            result = await dolibarr_api.update_ticket(ticket_id, arguments)
            return [types.TextContent(
                type="text",
                text=f"Ticket mis à jour avec succès. ID: {ticket_id}"
            )]
        
        elif name == "add_ticket_message":
            result = await dolibarr_api.add_ticket_message(arguments)
            return [types.TextContent(
                type="text",
                text=f"Message ajouté au ticket avec succès."
            )]
        
        elif name == "delete_ticket":
            ticket_id = arguments.get("ticket_id")
            result = await dolibarr_api.delete_ticket(ticket_id)
            return [types.TextContent(
                type="text",
                text=f"Ticket supprimé avec succès. ID: {ticket_id}"
            )]
        
        else:
            raise ValueError(f"Outil inconnu: {name}")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'appel de l'outil {name}: {str(e)}")
        return [types.TextContent(
            type="text",
            text=f"Erreur: {str(e)}"
        )]

async def main():
    """Point d'entrée principal"""
    logger.info("Démarrage du serveur MCP Dolibarr...")
    
    # Test de connexion à l'API
    try:
        logger.info("Test de connexion à l'API Dolibarr...")
        result = await dolibarr_api.search_contacts("", 1)
        logger.info("✅ Connexion à Dolibarr réussie")
    except Exception as e:
        logger.error(f"❌ Erreur de connexion à Dolibarr: {e}")
        logger.error("Vérifiez votre URL API et votre clé API")
        sys.exit(1)
    
    # Lancement du serveur MCP via stdio
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="dolibarr-mcp",
                server_version="1.2.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Arrêt du serveur MCP")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        sys.exit(1)
