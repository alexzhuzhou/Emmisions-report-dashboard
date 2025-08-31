from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, TIMESTAMP, func, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class Company(Base):
    __tablename__ = "companies"
    company_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_name = Column(String(100), unique=True, nullable=False, index=True)
    company_summary = Column(Text, nullable=False)
    website_url = Column(String(255), nullable=True)
    industry = Column(String(50), nullable=True)
    cso_linkedin_url = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    sustainability_metric = relationship("SustainabilityMetric", back_populates="company", uselist=False, cascade="all, delete-orphan")

class SustainabilityMetric(Base):
    __tablename__ = "sustainabilitymetrics"
    metric_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False, unique=True)
    owns_cng_fleet = Column(Boolean, nullable=False, default=False)
    cng_fleet_size_range = Column(Integer, nullable=False, default=0)
    cng_fleet_size_actual = Column(Integer, nullable=False, default=0)
    total_fleet_size = Column(Integer, nullable=False, default=0)
    emission_report = Column(Boolean, nullable=False, default=False)
    emission_goals = Column(Integer, nullable=False, default=0)
    alt_fuels = Column(Boolean, nullable=False, default=False)
    clean_energy_partners = Column(Boolean, nullable=False, default=False)
    regulatory_pressure = Column(Boolean, nullable=False, default=False)
    cng_adopt_score = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())

    company = relationship("Company", back_populates="sustainability_metric")
    metric_sources = relationship("MetricSource", back_populates="metric", cascade="all, delete-orphan")
    fleet_summary = relationship("FleetSummary", back_populates="metric", uselist=False, cascade="all, delete-orphan")
    emissions_summary = relationship("EmissionsSummary", back_populates="metric", uselist=False, cascade="all, delete-orphan")
    alt_fuels_summary = relationship("AltFuelsSummary", back_populates="metric", uselist=False, cascade="all, delete-orphan")
    clean_energy_partners_summary = relationship("CleanEnergyPartnersSummary", back_populates="metric", uselist=False, cascade="all, delete-orphan")
    regulatory_pressure_summary = relationship("RegulatoryPressureSummary", back_populates="metric", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("cng_fleet_size_range IN (0, 1, 2, 3)", name='valid_cng_fleet_size_range'),
        CheckConstraint("emission_goals IN (0, 1, 2)", name='valid_emission_goal'),
    )

class MetricSource(Base):
    __tablename__ = "metricsources"
    metric_source_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    metric_id = Column(Integer, ForeignKey("sustainabilitymetrics.metric_id", ondelete="CASCADE"), nullable=False)
    metric_name = Column(String(50), nullable=False)
    source_url = Column(Text, nullable=False)
    contribution_text = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    metric = relationship("SustainabilityMetric", back_populates="metric_sources")
    fleet_summaries = relationship("FleetSummary", back_populates="metric_source")
    emissions_summaries = relationship("EmissionsSummary", back_populates="metric_source")
    alt_fuels_summaries = relationship("AltFuelsSummary", back_populates="metric_source")
    clean_energy_partners_summaries = relationship("CleanEnergyPartnersSummary", back_populates="metric_source")
    regulatory_pressure_summaries = relationship("RegulatoryPressureSummary", back_populates="metric_source")

    __table_args__ = (
        UniqueConstraint('metric_id', 'metric_name', name='unique_metric_id_metric_name'),
        CheckConstraint(
            "metric_name IN ('owns_cng_fleet', 'cng_fleet_size_range', 'cng_fleet_size_actual', 'total_fleet_size', 'emission_report', 'emission_goals', 'alt_fuels', 'clean_energy_partners', 'regulatory_pressure')",
            name='valid_metric_name'
        ),
    )

class FleetSummary(Base):
    __tablename__ = "fleetsummary"
    fleet_summary_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    metric_id = Column(Integer, ForeignKey("sustainabilitymetrics.metric_id", ondelete="CASCADE"), nullable=False, unique=True)
    metric_source_id = Column(Integer, ForeignKey("metricsources.metric_source_id", ondelete="SET NULL"), nullable=True)
    metric_name = Column(String(50), nullable=False, default='owns_cng_fleet')
    summary_text = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    metric = relationship("SustainabilityMetric", back_populates="fleet_summary")
    metric_source = relationship("MetricSource", back_populates="fleet_summaries")

    __table_args__ = (
        CheckConstraint("metric_name = 'owns_cng_fleet'", name='valid_metric_name'),
    )

class EmissionsSummary(Base):
    __tablename__ = "emissionssummary"
    emissions_summary_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    metric_id = Column(Integer, ForeignKey("sustainabilitymetrics.metric_id", ondelete="CASCADE"), nullable=False, unique=True)
    metric_source_id = Column(Integer, ForeignKey("metricsources.metric_source_id", ondelete="SET NULL"), nullable=True)
    metric_name = Column(String(50), nullable=False, default='emission_report')
    emissions_summary = Column(Text, nullable=False)
    emissions_goals_summary = Column(Text, nullable=False)
    current_emissions = Column(Integer, default=0, nullable=True)
    target_year = Column(Integer, default=2040, nullable=True)
    target_emissions = Column(Integer, default=0, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    metric = relationship("SustainabilityMetric", back_populates="emissions_summary")
    metric_source = relationship("MetricSource", back_populates="emissions_summaries")

    __table_args__ = (
        CheckConstraint("metric_name = 'emission_report'", name='valid_metric_name'),
    )

class AltFuelsSummary(Base):
    __tablename__ = "altfuelssummary"
    alt_fuels_summary_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    metric_id = Column(Integer, ForeignKey("sustainabilitymetrics.metric_id", ondelete="CASCADE"), nullable=False, unique=True)
    metric_source_id = Column(Integer, ForeignKey("metricsources.metric_source_id", ondelete="SET NULL"), nullable=True)
    metric_name = Column(String(50), nullable=False, default='alt_fuels')
    summary_text = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    metric = relationship("SustainabilityMetric", back_populates="alt_fuels_summary")
    metric_source = relationship("MetricSource", back_populates="alt_fuels_summaries")

    __table_args__ = (
        CheckConstraint("metric_name = 'alt_fuels'", name='alt_fuels_summary_metric_name'),
    )

class CleanEnergyPartnersSummary(Base):
    __tablename__ = "cleanenergypartnerssummary"
    clean_energy_summary_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    metric_id = Column(Integer, ForeignKey("sustainabilitymetrics.metric_id", ondelete="CASCADE"), nullable=False, unique=True)
    metric_source_id = Column(Integer, ForeignKey("metricsources.metric_source_id", ondelete="SET NULL"), nullable=True)
    metric_name = Column(String(50), nullable=False, default='clean_energy_partners')
    summary_text = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    metric = relationship("SustainabilityMetric", back_populates="clean_energy_partners_summary")
    metric_source = relationship("MetricSource", back_populates="clean_energy_partners_summaries")

    __table_args__ = (
        CheckConstraint("metric_name = 'clean_energy_partners'", name='clean_energy_summary_metric_name'),
    )

class RegulatoryPressureSummary(Base):
    __tablename__ = "regulatorypressuresummary"
    regulatory_pressure_summary_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    metric_id = Column(Integer, ForeignKey("sustainabilitymetrics.metric_id", ondelete="CASCADE"), nullable=False, unique=True)
    metric_source_id = Column(Integer, ForeignKey("metricsources.metric_source_id", ondelete="SET NULL"), nullable=True)
    metric_name = Column(String(50), nullable=False, default='regulatory_pressure')
    summary_text = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    metric = relationship("SustainabilityMetric", back_populates="regulatory_pressure_summary")
    metric_source = relationship("MetricSource", back_populates="regulatory_pressure_summaries")

    __table_args__ = (
        CheckConstraint("metric_name = 'regulatory_pressure'", name='regulatory_pressure_summary_metric_name'),
    )