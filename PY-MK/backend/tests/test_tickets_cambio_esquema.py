from app.modules.support_tickets.schemas.support_ticket import (
    SupportTicketCreate,
    TicketClientDecision,
    TicketConvert,
    TicketEstimate,
)
from pydantic import ValidationError


def test_ticket_estimate_valid_values():
    """Test that TicketEstimate accepts valid hour values."""
    # Test valid values
    estimate = TicketEstimate(hours=0.5)
    assert estimate.hours == 0.5
    
    estimate = TicketEstimate(hours=9999)
    assert estimate.hours == 9999


def test_ticket_estimate_invalid_values():
    """Test that TicketEstimate raises ValidationError for invalid hour values."""
    # Test invalid values with parametrize
    invalid_values = [0, -1, 10000]
    
    for hours in invalid_values:
        try:
            TicketEstimate(hours=hours)
            assert False, f"Expected ValidationError for hours={hours}"
        except ValidationError:
            pass  # Expected


def test_ticket_estimate_note_too_long():
    """Test that TicketEstimate raises ValidationError when note exceeds max_length."""
    try:
        TicketEstimate(hours=2, note="x" * 1001)
        assert False, "Expected ValidationError for too long note"
    except ValidationError:
        pass  # Expected


def test_ticket_client_decision_valid_values():
    """Test that TicketClientDecision accepts valid decision values."""
    # Test valid decisions
    decision = TicketClientDecision(decision="approved")
    assert decision.decision == "approved"
    
    decision = TicketClientDecision(decision="rejected")
    assert decision.decision == "rejected"


def test_ticket_client_decision_invalid_value():
    """Test that TicketClientDecision raises ValidationError for invalid decision."""
    try:
        TicketClientDecision(decision="maybe")
        assert False, "Expected ValidationError for invalid decision"
    except ValidationError:
        pass  # Expected


def test_ticket_convert_valid_values():
    """Test that TicketConvert accepts valid values."""
    # Test without project (valid)
    convert = TicketConvert(assigned_user_id=1)
    assert convert.assigned_user_id == 1
    
    # Test with valid project name
    convert = TicketConvert(assigned_user_id=1, project_name="Migración")
    assert convert.project_name == "Migración"


def test_ticket_convert_invalid_project_name():
    """Test that TicketConvert raises ValidationError for invalid project name."""
    try:
        TicketConvert(assigned_user_id=1, project_name="ab")
        assert False, "Expected ValidationError for too short project name"
    except ValidationError:
        pass  # Expected


def test_support_ticket_create_kind_field():
    """Test that SupportTicketCreate validates kind field correctly."""
    # Test default kind
    ticket = SupportTicketCreate(title="Caída", priority="high")
    assert ticket.kind == "incidencia"
    
    # Test valid kind
    ticket = SupportTicketCreate(title="Caída", priority="high", kind="cambio")
    assert ticket.kind == "cambio"
    
    # Test invalid kind
    try:
        SupportTicketCreate(title="Caída", priority="high", kind="mejora")
        assert False, "Expected ValidationError for invalid kind"
    except ValidationError:
        pass  # Expected
