"""Kirby-only repeated text disabling and inherited command semantics."""
from unittest.mock import patch

import pytest

from worlds._bizhawk.context import BizHawkClientCommandProcessor, BizHawkClientContext, TextCategory

from ..client import KirbyAmClient, _build_kirbyam_command_processor, _patch_kirbyam_command_processor


def processor(*, patched=False, game=KirbyAmClient.game):
    # Avoid opening transports; this command needs only these context fields.
    ctx = object.__new__(BizHawkClientContext)
    ctx.game = game
    ctx.text_passthrough_categories = set()

    class Base(BizHawkClientCommandProcessor):
        pass

    cls = _patch_kirbyam_command_processor(Base) if patched else _build_kirbyam_command_processor(Base)
    return cls(ctx)


@pytest.mark.parametrize("patched", [False, True])
@pytest.mark.parametrize("category", [value.value for value in TextCategory if value != TextCategory.ALL])
def test_repeated_disable_is_idempotent(category, patched):
    command = processor(patched=patched)
    categories = command.ctx.text_passthrough_categories
    with patch("worlds._bizhawk.context.logger.info") as output:
        command(f"/toggle_text {category} on")
        command(f"/toggle_text {category} off")
        command(f"/toggle_text {category.upper()} FALSE")
        command(f"/toggle_text {category} off")
    assert command.ctx.text_passthrough_categories is categories
    assert categories == set()
    assert output.call_count == 4
    assert output.call_args.args == ("Currently Showing Categories: ",)


@pytest.mark.parametrize("patched", [False, True])
def test_default_toggle_all_and_validation_remain_inherited(patched):
    command = processor(patched=patched)
    command._cmd_toggle_text("chat")
    assert command.ctx.text_passthrough_categories == {"chat"}
    command._cmd_toggle_text("chat")
    assert command.ctx.text_passthrough_categories == set()
    command._cmd_toggle_text("ALL", "true")
    assert command.ctx.text_passthrough_categories == set(TextCategory) - {TextCategory.ALL}
    with patch("worlds._bizhawk.context.logger.info") as output:
        command._cmd_toggle_text("all")
        command._cmd_toggle_text("bad", "off")
        command._cmd_toggle_text("chat", "bad")
        command._cmd_toggle_text()
    messages = [entry.args[0] for entry in output.call_args_list]
    assert messages[0] == 'Must specify "on" or "off" for category "all"'
    assert messages[1].startswith('Unknown value "bad", should be all|')
    assert messages[2] == 'Unknown value "bad", should be on|off|true|false'
    assert messages[3].startswith("Usage: /toggle_text")
    command._cmd_toggle_text("all", "off")
    command._cmd_toggle_text("all", "off")
    assert command.ctx.text_passthrough_categories == set()


@pytest.mark.parametrize("patched", [False, True])
def test_other_game_still_uses_shared_behavior_after_slot_change(patched):
    command = processor(patched=patched)
    command._cmd_toggle_text("chat", "off")
    command.ctx.game = "Other Game"
    with pytest.raises(KeyError, match="chat"):
        command._cmd_toggle_text("chat", "off")


def test_disabling_absent_category_preserves_other_messages():
    command = processor()
    command.ctx.text_passthrough_categories = {"server"}
    with patch("worlds._bizhawk.context.logger.info") as output:
        command("/toggle_text chat off")
    assert command.ctx.text_passthrough_categories == {"server"}
    output.assert_called_once_with("Currently Showing Categories: server")
