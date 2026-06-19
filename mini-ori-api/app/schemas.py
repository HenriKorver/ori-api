from datetime import date, datetime
from typing import Optional, Union

from pydantic import BaseModel, Field


class Gemeente(BaseModel):
    gemeente: str = Field(..., examples=["gm0363"])
    naam: str = Field(..., examples=["Gemeente Amsterdam"])


class Provincie(BaseModel):
    provincie: str = Field(..., examples=["pv27"])
    naam: str = Field(..., examples=["Provincie Groningen"])


class Waterschap(BaseModel):
    waterschap: str = Field(..., examples=["ws0654"])
    naam: str = Field(..., examples=["Waterschap Aa en Maas"])


Organisatie = Union[Gemeente, Provincie, Waterschap]


class VerwijzingNaarResource(BaseModel):
    id: str
    url: str


class Gremium(BaseModel):
    gremiumidentificatie: str
    gremiumnaam: str


class GerelateerdInformatieobject(BaseModel):
    informatieobject: str
    rol: str


class AgendapuntZonderPid(BaseModel):
    webpaginalink: Optional[str] = None
    organisatie: Organisatie
    dossiertype: str
    agendapuntnaam: str
    vergadering: str
    hoofdagendapunt: Optional[str] = None
    omschrijving: Optional[str] = None
    volgnummer: Optional[str] = None
    subagendapunten: Optional[list[str]] = None
    tussenkop: Optional[str] = None
    overig: Optional[str] = None
    starttijd: Optional[datetime] = None
    eindtijd: Optional[datetime] = None
    locatie: Optional[str] = None
    geplandvolgnummer: Optional[str] = None
    geplandeeindtijd: Optional[datetime] = None
    geplandestarttijd: Optional[datetime] = None
    indicatiehamerstuk: Optional[bool] = None
    indicatiebehandeld: Optional[bool] = None
    indicatiebesloten: Optional[bool] = None


class Agendapunt(BaseModel):
    id: str
    url: str
    vergaderingen: list[VerwijzingNaarResource]
    webpaginalink: Optional[str] = None
    organisatie: Organisatie
    dossiertype: str
    agendapuntnaam: str
    hoofdagendapunt: Optional[VerwijzingNaarResource] = None
    omschrijving: Optional[str] = None
    volgnummer: Optional[str] = None
    subagendapunten: Optional[list[str]] = None
    tussenkop: Optional[str] = None
    overig: Optional[str] = None
    starttijd: Optional[datetime] = None
    eindtijd: Optional[datetime] = None
    locatie: Optional[str] = None
    geplandvolgnummer: Optional[str] = None
    geplandeeindtijd: Optional[datetime] = None
    geplandestarttijd: Optional[datetime] = None
    indicatiehamerstuk: Optional[bool] = None
    indicatiebehandeld: Optional[bool] = None
    indicatiebesloten: Optional[bool] = None
    informatieobjecten: list[str] = []


class InformatieObjectZonderPid(BaseModel):
    agendapunt: Optional[str] = None
    vergadering: Optional[str] = None
    webpaginalink: str
    organisatie: Organisatie
    titel: str
    wooinformatiecategorie: str
    datumingediend: date
    id: Optional[str] = None
    auteur: Optional[str] = None
    bronorganisatie: Optional[str] = None
    creatiedatum: Optional[str] = None
    informatieobjecttype: Optional[str] = None
    formaat: Optional[str] = None
    omschrijving: Optional[str] = None
    taal: Optional[str] = None
    gerelateerdinformatieobject: Optional[GerelateerdInformatieobject] = None


class InformatieObject(BaseModel):
    id: str
    url: str
    webpaginalink: str
    organisatie: Organisatie
    titel: str
    wooinformatiecategorie: str
    datumingediend: date
    auteur: Optional[str] = None
    bronorganisatie: Optional[str] = None
    creatiedatum: Optional[str] = None
    informatieobjecttype: Optional[str] = None
    formaat: Optional[str] = None
    omschrijving: Optional[str] = None
    taal: Optional[str] = None
    vergaderingen: list[VerwijzingNaarResource] = []
    agendapunten: list[VerwijzingNaarResource] = []
    gerelateerdinformatieobject: Optional[GerelateerdInformatieobject] = None


class VergaderingZonderPid(BaseModel):
    webpaginalink: Optional[str] = None
    organisatie: Organisatie
    dossiertype: str
    naam: str
    aanvang: Optional[datetime] = None
    hoofdvergadering: Optional[VerwijzingNaarResource] = None
    einde: Optional[datetime] = None
    georganiseerddoorgremium: Optional[Gremium] = None
    geplandeaanvang: Optional[datetime] = None
    geplandeeinde: Optional[datetime] = None
    geplandedatum: Optional[date] = None
    locatie: Optional[str] = None
    vergaderstatus: Optional[str] = None
    vergadertoelichting: Optional[str] = None
    vergaderdatum: Optional[date] = None
    vergaderingstype: Optional[str] = None
    deelvergaderingen: Optional[list[str]] = None


class Vergadering(BaseModel):
    id: str
    url: str
    webpaginalink: Optional[str] = None
    organisatie: Organisatie
    dossiertype: str
    naam: str
    aanvang: Optional[datetime] = None
    hoofdvergadering: Optional[VerwijzingNaarResource] = None
    einde: Optional[datetime] = None
    georganiseerddoorgremium: Optional[Gremium] = None
    geplandeaanvang: Optional[datetime] = None
    geplandeeinde: Optional[datetime] = None
    geplandedatum: Optional[date] = None
    locatie: Optional[str] = None
    vergaderstatus: Optional[str] = None
    vergadertoelichting: Optional[str] = None
    vergaderdatum: Optional[date] = None
    vergaderingstype: Optional[str] = None
    deelvergaderingen: list[str] = []


class PaginatedAgendapuntList(BaseModel):
    next: Optional[str] = None
    previous: Optional[str] = None
    results: list[Agendapunt]


class PaginatedInformatieObjectList(BaseModel):
    next: Optional[str] = None
    previous: Optional[str] = None
    results: list[InformatieObject]


class PaginatedVergaderingList(BaseModel):
    next: Optional[str] = None
    previous: Optional[str] = None
    results: list[Vergadering]


class ErrorResponse(BaseModel):
    titel: str
    status: int
    detail: str
