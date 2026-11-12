#!/usr/bin/env bash
# Regression tests for the skill's scripts. A good blueprint must pass, a slideshow must fail,
# and a blueprint compared with itself must be flagged as a clone.
set -u
cd "$(dirname "$0")/.."
fail=0
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
python3 scripts/blueprint_check.py tests/fixtures/good_blueprint.json >$T/vm_good.txt || { echo "FAIL good blueprint should pass"; cat $T/vm_good.txt; fail=1; }
python3 scripts/blueprint_check.py tests/fixtures/slideshow_blueprint.json >$T/vm_bad.txt && { echo "FAIL slideshow should fail"; fail=1; }
for want in "banned phrase" "opens on a title card" "stock is" "gate 1" "signature yellow" "cites no dossier claim"; do
  grep -q "$want" $T/vm_bad.txt || { echo "FAIL slideshow report lacks: $want"; fail=1; }
done
python3 scripts/blueprint_check.py tests/fixtures/good_blueprint.json --compare tests/fixtures/good_blueprint.json >$T/vm_same.txt && { echo "FAIL self-compare should fail"; fail=1; }
grep -q "repeats" $T/vm_same.txt || { echo "FAIL self-compare names no repeat"; fail=1; }
python3 scripts/render_blueprint.py tests/fixtures/good_blueprint.json -o $T/vm_good.md >/dev/null && grep -q "Edit list" $T/vm_good.md || { echo "FAIL render"; fail=1; }
echo '[{"id":"S1","narration":"x","need":"specific_place","have_evidence":true},{"id":"S2","narration":"y","need":"share_of_whole"}]' > $T/vm_beats.json
python3 scripts/visual_decide.py $T/vm_beats.json --domain geography --avoid map_globe | grep -q "satellite" || { echo "FAIL visual_decide"; fail=1; }
echo '{"title":"w","channel":"print-facts","central_question":"q","answer":"a","hook":{"x":1},"dna":{},"chapters":[],"scenes":[{"id":"S1","start":0,"end":3,"narration":"It uses two hundred million litres.","visual_mode":"satellite","asset_ids":["a"]}]}' > $T/vm_words.json
python3 scripts/blueprint_check.py $T/vm_words.json --profile generic | grep -q "two hundred million" || { echo "FAIL spelled-out number not caught"; fail=1; }
python3 scripts/history_stubs.py --repo ../../.. --out $T/stubs >/dev/null || { echo "FAIL history_stubs"; fail=1; }
[ $fail -eq 0 ] && echo "ALL TESTS PASS"
exit $fail
