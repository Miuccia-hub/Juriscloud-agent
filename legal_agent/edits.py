from .models import EditChoice


def accepted(choices):
    return [c for c in choices if c.state == "采纳"]


def check_conflicts(main,choices):
    clauses = {c.id:c for c in main.clauses}
    errors, ranges = [], {}
    for choice in accepted(choices):
        edit = choice.edit
        if choice.needs_reconfirmation:
            errors.append(f"{edit.id} 受新事实或新建议影响，请重新确认。")
        clause = clauses.get(edit.clause_id)
        if not clause or not edit.original or clause.text.count(edit.original) != 1:
            errors.append(f"{edit.id} 无法唯一定位。")
            continue
        start = clause.text.index(edit.original)
        end = start + len(edit.original)
        for a,b,old in ranges.get(edit.clause_id,[]):
            if start < b and a < end:
                errors.append(f"{old} 与 {edit.id} 修改范围重叠，请只采纳其中一项。")
        ranges.setdefault(edit.clause_id,[]).append((start,end,edit.id))
    return errors


def merge_choices(choices,new_edits,origin,new_facts=False):
    for choice in choices:
        if choice.state == "采纳" and (new_facts or any(e.clause_id == choice.edit.clause_id for e in new_edits)):
            choice.needs_reconfirmation = True
    choices.extend(EditChoice(e,replacement=e.replacement,origin=origin) for e in new_edits)
    return choices
