from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class AgendapuntInformatieObjectLink(SQLModel, table=True):
    __tablename__ = "agendapunt_informatieobject_link"

    agendapunt_id: Optional[int] = Field(
        default=None,
        foreign_key="agendapunten.id",
        primary_key=True,
    )
    informatieobject_id: Optional[int] = Field(
        default=None,
        foreign_key="informatieobjecten.id",
        primary_key=True,
    )


class VergaderingDB(SQLModel, table=True):
    __tablename__ = "vergaderingen"

    id: Optional[int] = Field(default=None, primary_key=True)
    public_id: str = Field(index=True, unique=True)
    url: str = Field(index=True, unique=True)

    webpaginalink: Optional[str] = None
    organisatie_type: str
    organisatie_code: str
    organisatie_naam: str

    dossiertype: str
    naam: str
    aanvang: Optional[datetime] = None
    einde: Optional[datetime] = None

    hoofdvergadering_id: Optional[int] = Field(default=None, foreign_key="vergaderingen.id")

    gremium_identificatie: Optional[str] = None
    gremium_naam: Optional[str] = None

    geplandeaanvang: Optional[datetime] = None
    geplandeeinde: Optional[datetime] = None
    geplandedatum: Optional[date] = None
    locatie: Optional[str] = None
    vergaderstatus: Optional[str] = None
    vergadertoelichting: Optional[str] = None
    vergaderdatum: Optional[date] = None
    vergaderingstype: Optional[str] = None

    agendapunten: list["AgendapuntDB"] = Relationship(back_populates="vergadering")
    informatieobjecten: list["InformatieObjectDB"] = Relationship(back_populates="vergadering")

    hoofdvergadering: Optional["VergaderingDB"] = Relationship(
        back_populates="deelvergaderingen",
        sa_relationship_kwargs={"remote_side": "VergaderingDB.id"},
    )
    deelvergaderingen: list["VergaderingDB"] = Relationship(back_populates="hoofdvergadering")


class AgendapuntDB(SQLModel, table=True):
    __tablename__ = "agendapunten"

    id: Optional[int] = Field(default=None, primary_key=True)
    public_id: str = Field(index=True, unique=True)
    url: str = Field(index=True, unique=True)

    webpaginalink: Optional[str] = None
    organisatie_type: str
    organisatie_code: str
    organisatie_naam: str

    dossiertype: str
    agendapuntnaam: str
    vergadering_id: Optional[int] = Field(default=None, foreign_key="vergaderingen.id")
    hoofdagendapunt_id: Optional[int] = Field(default=None, foreign_key="agendapunten.id")

    omschrijving: Optional[str] = None
    volgnummer: Optional[str] = None
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

    vergadering: Optional[VergaderingDB] = Relationship(back_populates="agendapunten")
    hoofdagendapunt: Optional["AgendapuntDB"] = Relationship(
        back_populates="subagendapunten",
        sa_relationship_kwargs={"remote_side": "AgendapuntDB.id"},
    )
    subagendapunten: list["AgendapuntDB"] = Relationship(back_populates="hoofdagendapunt")

    informatieobjecten: list["InformatieObjectDB"] = Relationship(
        back_populates="agendapunten",
        link_model=AgendapuntInformatieObjectLink,
    )


class InformatieObjectDB(SQLModel, table=True):
    __tablename__ = "informatieobjecten"

    id: Optional[int] = Field(default=None, primary_key=True)
    public_id: str = Field(index=True, unique=True)
    url: str = Field(index=True, unique=True)

    webpaginalink: str
    organisatie_type: str
    organisatie_code: str
    organisatie_naam: str

    titel: str
    wooinformatiecategorie: str
    datumingediend: date

    external_id: Optional[str] = None
    auteur: Optional[str] = None
    bronorganisatie: Optional[str] = None
    creatiedatum: Optional[str] = None
    informatieobjecttype: Optional[str] = None
    formaat: Optional[str] = None
    omschrijving: Optional[str] = None
    taal: Optional[str] = None

    gerelateerd_informatieobject_id: Optional[str] = None
    gerelateerd_rol: Optional[str] = None

    vergadering_id: Optional[int] = Field(default=None, foreign_key="vergaderingen.id")

    vergadering: Optional[VergaderingDB] = Relationship(back_populates="informatieobjecten")
    agendapunten: list[AgendapuntDB] = Relationship(
        back_populates="informatieobjecten",
        link_model=AgendapuntInformatieObjectLink,
    )
