"""
apple_calendar_service.py
Serviço de integração com Apple Calendar via CalDAV — pronto para FastAPI.

Dependências:
    pip install caldav icalendar pytz

Uso no FastAPI:
    from apple_calendar_service import AppleCalendarService, CalendarError

    svc = AppleCalendarService(apple_id="user@icloud.com", app_password="xxxx-xxxx-xxxx-xxxx")
    uid = svc.create_event(calendar_name="Consultas", title="Consulta", start=..., end=...)
"""

import uuid
import caldav
import pytz
from datetime import datetime, timedelta
from icalendar import Calendar, Event, vText


APPLE_CALDAV_URL = "https://caldav.icloud.com"

# Calendários nativos da Apple que são somente-leitura
_READONLY_CALENDAR_NAMES = {
    "birthdays", "anniversaries", "siri suggestions",
    "found in apps", "holidays in brazil", "feriados no brasil",
    "holidays", "feriados", "lembretes",
}


class CalendarError(Exception):
    """Erros esperados da integração Apple Calendar (credencial inválida, calendário não encontrado, etc.)"""
    pass


class AppleCalendarService:
    """
    Serviço stateless para operações no Apple Calendar via CalDAV.

    Cada método cria uma nova conexão com o iCloud — não reutiliza conexões
    entre chamadas para evitar keepalive timeout (comportamento esperado da Apple).

    Args:
        apple_id:     E-mail da conta Apple do usuário.
        app_password: App-Specific Password gerada em appleid.apple.com.
        timezone:     Fuso padrão para eventos sem timezone explícito.
    """

    def __init__(self, apple_id: str, app_password: str, timezone: str = "America/Sao_Paulo"):
        self.apple_id     = apple_id
        self.app_password = app_password
        self.timezone     = timezone

    # ─────────────────────────────────────────────
    # CONEXÃO (privado)
    # ─────────────────────────────────────────────

    def _client(self) -> caldav.DAVClient:
        """Abre uma nova conexão CalDAV autenticada."""
        return caldav.DAVClient(
            url=APPLE_CALDAV_URL,
            username=self.apple_id,
            password=self.app_password,
        )

    def _get_calendar(self, client: caldav.DAVClient, calendar_name: str):
        """Retorna o objeto caldav.Calendar pelo nome."""
        try:
            principal = client.principal()
            calendars = principal.calendars()
        except caldav.lib.error.AuthorizationError:
            raise CalendarError("Credenciais inválidas. Verifique o Apple ID e a App-Specific Password.")

        if not calendars:
            raise CalendarError("Nenhum calendário encontrado para este usuário.")

        calendar_name = calendar_name.strip()
        for cal in calendars:
            if cal.get_display_name().strip() == calendar_name:
                return cal

        raise CalendarError(f"Calendário '{calendar_name}' não encontrado.")

    # ─────────────────────────────────────────────
    # CALENDÁRIOS
    # ─────────────────────────────────────────────

    def validate_credentials(self) -> bool:
        """
        Testa se as credenciais são válidas conectando ao iCloud.
        Use no onboarding para confirmar que o usuário inseriu os dados corretos.

        Returns:
            True se autenticou com sucesso.

        Raises:
            CalendarError: Se as credenciais forem inválidas.
        """
        try:
            client = self._client()
            client.principal()
            return True
        except caldav.lib.error.AuthorizationError:
            raise CalendarError("Credenciais inválidas. Verifique o Apple ID e a App-Specific Password.")

    def list_calendars(self) -> list[dict]:
        """
        Lista todos os calendários do usuário com nome, URL e flag de gravável.

        Returns:
            Lista de dicts: [{"name": str, "url": str, "writable": bool}]
        """
        client    = self._client()
        principal = client.principal()
        calendars = principal.calendars()

        result = []
        for cal in calendars:
            name = cal.get_display_name().strip()
            result.append({
                "name":     name,
                "url":      str(cal.url),
                "writable": name.lower() not in _READONLY_CALENDAR_NAMES,
            })
        return result

    def create_calendar(self, name: str) -> dict:
        """
        Cria um novo calendário no iCloud.
        Execute uma única vez no onboarding do usuário.

        Args:
            name: Nome do calendário (ex: "Consultas MeuSaaS").

        Returns:
            Dict com name e url do calendário criado.
        """
        client    = self._client()
        principal = client.principal()
        cal = principal.make_calendar(
            name=name,
            cal_id=str(uuid.uuid4()),
            supported_calendar_component_set=["VEVENT"],
        )
        return {"name": name, "url": str(cal.url)}

    # ─────────────────────────────────────────────
    # EVENTOS
    # ─────────────────────────────────────────────

    def create_event(
        self,
        calendar_name: str,
        title: str,
        start: datetime,
        end: datetime,
        description: str = "",
        location: str = "",
    ) -> str:
        """
        Cria um evento no calendário especificado.

        Args:
            calendar_name: Nome exato do calendário de destino.
            title:         Título do evento.
            start:         Datetime de início (com ou sem timezone).
            end:           Datetime de fim (com ou sem timezone).
            description:   Descrição opcional.
            location:      Local opcional.

        Returns:
            UID do evento criado (salve no banco para editar/deletar depois).

        Raises:
            CalendarError: Se calendário não encontrado ou credenciais inválidas.
        """
        tz = pytz.timezone(self.timezone)
        if start.tzinfo is None:
            start = tz.localize(start)
        if end.tzinfo is None:
            end = tz.localize(end)

        event_uid = str(uuid.uuid4())

        cal = Calendar()
        cal.add("prodid", "-//LashFlow//BR")
        cal.add("version", "2.0")

        event = Event()
        event.add("summary", title)
        event.add("dtstart", start)
        event.add("dtend", end)
        event.add("dtstamp", datetime.now(tz=pytz.utc))
        event.add("uid", event_uid)
        if description:
            event.add("description", description)
        if location:
            event.add("location", vText(location))

        cal.add_component(event)

        client   = self._client()
        calendar = self._get_calendar(client, calendar_name)
        calendar.save_event(cal.to_ical())

        return event_uid

    def update_event(
        self,
        calendar_name: str,
        uid: str,
        title: str = None,
        start: datetime = None,
        end: datetime = None,
        description: str = None,
        location: str = None,
    ) -> bool:
        """
        Atualiza um evento existente pelo UID.

        Args:
            calendar_name: Nome do calendário onde o evento está.
            uid:           UID do evento (retornado por create_event).
            title:         Novo título (None = não altera).
            start:         Novo início (None = não altera).
            end:           Novo fim (None = não altera).
            description:   Nova descrição (None = não altera).
            location:      Novo local (None = não altera).

        Returns:
            True se encontrou e atualizou, False se não encontrou o UID.
        """
        tz = pytz.timezone(self.timezone)

        client   = self._client()
        calendar = self._get_calendar(client, calendar_name)

        now   = datetime.now(tz=pytz.utc)
        until = now + timedelta(days=365)
        results = calendar.date_search(start=now, end=until, expand=True)

        for result in results:
            cal_data = Calendar.from_ical(result.data)
            for component in cal_data.walk():
                if component.name == "VEVENT" and str(component.get("uid", "")) == uid:
                    if title is not None:
                        component["summary"] = vText(title)
                    if start is not None:
                        s = tz.localize(start) if start.tzinfo is None else start
                        component["dtstart"].dt = s
                    if end is not None:
                        e = tz.localize(end) if end.tzinfo is None else end
                        component["dtend"].dt = e
                    if description is not None:
                        component["description"] = vText(description)
                    if location is not None:
                        component["location"] = vText(location)

                    result.data = cal_data.to_ical()
                    result.save()
                    return True

        return False

    def delete_event(self, calendar_name: str, uid: str) -> bool:
        """
        Deleta um evento pelo UID.

        Args:
            calendar_name: Nome do calendário onde o evento está.
            uid:           UID do evento (retornado por create_event).

        Returns:
            True se encontrou e deletou, False se não encontrou o UID.
        """
        client   = self._client()
        calendar = self._get_calendar(client, calendar_name)

        now   = datetime.now(tz=pytz.utc)
        until = now + timedelta(days=365)
        results = calendar.date_search(start=now, end=until, expand=True)

        for result in results:
            cal_data = Calendar.from_ical(result.data)
            for component in cal_data.walk():
                if component.name == "VEVENT" and str(component.get("uid", "")) == uid:
                    result.delete()
                    return True

        return False
