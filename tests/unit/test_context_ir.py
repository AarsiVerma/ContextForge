"""Unit tests for ContextIR model."""

from contextforge.models import (
    ContextIR,
    ContextItem,
    ContextType,
    ItemStatus,
    Provenance,
)


def make_item(type_: ContextType, content: str, task_id: str = "task-123") -> ContextItem:
    """Helper to create a test item."""
    prov = Provenance.from_file("test.py", "user1", task_id)
    return ContextItem(type=type_, content=content, source="test.py", provenance=prov)


def test_context_ir_creation() -> None:
    """Test basic ContextIR creation."""
    ir = ContextIR(task_id="task-123", task_description="Debug login issue")

    assert ir.id is not None
    assert ir.version == "0.1.0"
    assert ir.task_id == "task-123"
    assert ir.task_description == "Debug login issue"
    assert ir.items == []


def test_context_ir_add_item() -> None:
    """Test adding items to ContextIR."""
    ir = ContextIR(task_id="task-123", task_description="Test")
    item = make_item(ContextType.EVIDENCE, "Test evidence")

    ir.add_item(item)

    assert len(ir.items) == 1
    assert ir.items[0] == item


def test_context_ir_get_items_by_type() -> None:
    """Test filtering items by type."""
    ir = ContextIR(task_id="task-123", task_description="Test")
    ir.add_item(make_item(ContextType.EVIDENCE, "Evidence 1"))
    ir.add_item(make_item(ContextType.FACT, "Fact 1"))
    ir.add_item(make_item(ContextType.EVIDENCE, "Evidence 2"))
    ir.add_item(make_item(ContextType.HYPOTHESIS, "Hypothesis 1"))

    evidence = ir.get_items_by_type(ContextType.EVIDENCE)
    facts = ir.get_items_by_type(ContextType.FACT)
    hyps = ir.get_items_by_type(ContextType.HYPOTHESIS)

    assert len(evidence) == 2
    assert len(facts) == 1
    assert len(hyps) == 1


def test_context_ir_get_items_by_status() -> None:
    """Test filtering items by status."""
    ir = ContextIR(task_id="task-123", task_description="Test")
    item1 = make_item(ContextType.EVIDENCE, "Verified")
    item1.status = ItemStatus.VERIFIED
    item2 = make_item(ContextType.EVIDENCE, "Unverified")
    item3 = make_item(ContextType.EVIDENCE, "Rejected")
    item3.status = ItemStatus.REJECTED

    ir.add_item(item1)
    ir.add_item(item2)
    ir.add_item(item3)

    verified = ir.get_items_by_status(ItemStatus.VERIFIED)
    unverified = ir.get_items_by_status(ItemStatus.UNVERIFIED)
    rejected = ir.get_items_by_status(ItemStatus.REJECTED)

    assert len(verified) == 1
    assert len(unverified) == 1
    assert len(rejected) == 1


def test_context_ir_get_item() -> None:
    """Test getting item by ID."""
    ir = ContextIR(task_id="task-123", task_description="Test")
    item = make_item(ContextType.EVIDENCE, "Test")
    ir.add_item(item)

    found = ir.get_item(item.id)
    assert found == item

    not_found = ir.get_item("non-existent")
    assert not_found is None


def test_context_ir_remove_item() -> None:
    """Test removing item by ID."""
    ir = ContextIR(task_id="task-123", task_description="Test")
    item = make_item(ContextType.EVIDENCE, "Test")
    ir.add_item(item)

    result = ir.remove_item(item.id)
    assert result is True
    assert len(ir.items) == 0

    result = ir.remove_item("non-existent")
    assert result is False


def test_context_ir_serialization() -> None:
    """Test JSON serialization/deserialization."""
    ir = ContextIR(task_id="task-123", task_description="Test")
    ir.add_item(make_item(ContextType.EVIDENCE, "Evidence"))
    ir.add_item(make_item(ContextType.FACT, "Fact"))

    json_str = ir.to_json()
    assert isinstance(json_str, str)

    ir2 = ContextIR.from_json(json_str)
    assert ir2.task_id == ir.task_id
    assert ir2.task_description == ir.task_description
    assert len(ir2.items) == 2
    assert ir2.items[0].content == "Evidence"
    assert ir2.items[1].content == "Fact"


def test_context_ir_dict_conversion() -> None:
    """Test dict conversion."""
    ir = ContextIR(task_id="task-123", task_description="Test")
    ir.add_item(make_item(ContextType.EVIDENCE, "Test"))

    d = ir.to_dict()
    assert isinstance(d, dict)
    assert d["task_id"] == "task-123"

    ir2 = ContextIR.from_dict(d)
    assert ir2.task_id == "task-123"
    assert len(ir2.items) == 1
