"""Anything a script names, anywhere: buildings drawn as their type in their region's architecture (not a box),
crowds as a real group, places not mistaken for people, and vehicles that leave driving off on screen."""
from creatorforge_worker.animation import asset_lib as A, places as P, production, studio


def test_any_building_anywhere_is_its_type_in_its_regions_architecture():
    cases = {"Lok Sabha": ("legislature", "south_asia"), "US Capitol": ("legislature", "north_america"),
             "Kenya parliament": ("legislature", "africa"), "Jama Masjid": ("mosque", "middle_east"),
             "a temple in Kyoto": ("temple", "east_asia"), "a temple in Varanasi": ("temple", "south_asia"),
             "a church in Moscow": ("church", "russia"), "Notre Dame cathedral": ("church", "europe"),
             "police station": ("police", "modern"), "Taj Mahal tomb": ("tomb", "south_asia"),
             "nuclear power plant": ("power", "modern"), "a farm in Brazil": ("farm", "latin_america"),
             "refugee camp in Gaza": ("camp", "middle_east"), "संसद भवन": ("legislature", "south_asia"),
             "चुनाव आयोग": ("civic", "south_asia"), "Tokyo station": ("station", "east_asia")}
    for phrase, (kind, region) in cases.items():
        a = A.generate(phrase)
        assert (a["archetype"], a["region"]) == (kind, region), phrase
        assert not A.errors(A.validate(a)), phrase                     # closed, touching, standing, renders
        assert any(p["id"] == "board" for p in a["parts"]) and a["text"]   # its name on a plaque
    assert A.generate("the parliament", region="africa")["region"] == "africa"     # the script's region
    # ordinary things are not buildings ("small" is not a mall, "woman" is not Oman)
    assert A.generate("a small red car")["kind"] == "car"
    assert P.kind_of("a woman") is None and P.region_of("a woman in a period drama") == "modern"


def test_crowds_march_places_are_not_people_and_vehicles_leave_on_screen():
    doc, notes = studio.make("Thousands of workers march to the parliament in Delhi. Jordan walks to the market "
                             "in Amman. Raj runs to the bus stop. The bus leaves without him.", style="signature")
    s1, s2, s3, s4 = doc["scenes"]
    assert [(c["name"], c.get("crowd")) for c in s1["cast"]] == [("Crowd", 12)]   # a group, not "Delhi"
    assert any(st.get("verb") == "march" and st.get("who") == "Crowd" for st in s1["steps"])
    assert s1["things"] == ["parliament"] and s1["region"] == "south_asia"
    assert [c["name"] for c in s2["cast"]] == ["Jordan"] and s2["region"] == "middle_east"   # a name, a place
    assert s3["things"] == ["bus stop"] and s4["things"] == ["bus"]
    states = production.plan_states(doc, "preview")
    sc, T, _, _ = production.stage_scene(production.scenes_of(doc)[3], states[3][6], 24, "preview")
    bus = next(a for a in sc.actors if getattr(a, "name", "") == "bus")
    raj = next(a for a in sc.actors if getattr(a, "look", None) and a.look.name == "Raj")
    x0, x1 = bus.pos(0.0)[0], bus.pos(T)[0]
    assert abs(x0 - raj.hips_x(0.0)) < 5 and abs(x1 - x0) > 12  # beside him in the shot, then driven away
    sc, T, _, _ = production.stage_scene(production.scenes_of(doc)[0], states[0][6], 24, "preview")
    crowd = [a for a in sc.actors if getattr(a, "look", None) and a.look.name.startswith("Crowd")]
    assert len(crowd) == 12 and all(a.hips_x(T) - a.hips_x(0.0) > 4 for a in crowd)   # they all march in


def test_any_everyday_object_is_drawn_not_boxed():
    from creatorforge_worker.animation import objects as O
    for phrase, picture in {"a laptop": "personal computer", "ballot papers": "ballot box with ballot",
                            "a sword": "crossed swords", "the vaccine": "syringe", "a tractor tyre": "wheel",
                            "a court order": "scroll", "handcuffs": "chains", "तलवार": "crossed swords",
                            "वोट": "ballot box with ballot", "a flag": "waving white flag"}.items():
        a = A.generate(phrase)
        assert a["kind"] == "object" and a["picture"] == picture, phrase
        assert not A.errors(A.validate(a)), phrase                     # it renders, stands, plausible size
    assert A.generate("a laptop")["w"] < 1.0 and A.generate("a tractor")["kind"] == "car"   # sizes, generators win
    assert O.find("a man") is None and O.find("his face") is None      # people are characters, never pictures
    assert all(not O._never(n) for _, n, _ in O._index()) and not any("REGIONAL" in n for _, n, _ in O._index())
    assert A.Library(None).obtain("a zorbulating flux capacitor")[1] == "placeholder"   # never invents
