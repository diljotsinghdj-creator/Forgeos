#!/usr/bin/env bash
# Regression tests for the skill's scripts. A good blueprint must pass, a slideshow must fail,
# and a blueprint compared with itself must be flagged as a clone.
set -u
cd "$(dirname "$0")/.."
fail=0
python3 scripts/blueprint_check.py tests/fixtures/good_blueprint.json >/tmp/vm_good.txt || { echo "FAIL good blueprint should pass"; cat /tmp/vm_good.txt; fail=1; }
python3 scripts/blueprint_check.py tests/fixtures/slideshow_blueprint.json >/tmp/vm_bad.txt && { echo "FAIL slideshow should fail"; fail=1; }
for want in "banned phrase" "opens on a title card" "stock is" "gate 1" "signature yellow" "cites no dossier claim"; do
  grep -q "$want" /tmp/vm_bad.txt || { echo "FAIL slideshow report lacks: $want"; fail=1; }
done
python3 scripts/blueprint_check.py tests/fixtures/good_blueprint.json --compare tests/fixtures/good_blueprint.json >/tmp/vm_same.txt && { echo "FAIL self-compare should fail"; fail=1; }
grep -q "repeats" /tmp/vm_same.txt || { echo "FAIL self-compare names no repeat"; fail=1; }
python3 scripts/render_blueprint.py tests/fixtures/good_blueprint.json -o /tmp/vm_good.md >/dev/null && grep -q "Edit list" /tmp/vm_good.md || { echo "FAIL render"; fail=1; }
echo '[{"id":"S1","narration":"x","need":"specific_place","have_evidence":true},{"id":"S2","narration":"y","need":"share_of_whole"}]' > /tmp/vm_beats.json
python3 scripts/visual_decide.py /tmp/vm_beats.json --domain geography --avoid map_globe | grep -q "satellite" || { echo "FAIL visual_decide"; fail=1; }
[ $fail -eq 0 ] && echo "ALL TESTS PASS"
exit $fail
