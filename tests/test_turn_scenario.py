from demo.turn import label_scenario


def test_label_a_easy():
    assert label_scenario(force_local=False, has_pii=False, difficulty="easy") == (
        "A",
        "Easy → local",
    )


def test_label_b_hard():
    assert label_scenario(force_local=False, has_pii=False, difficulty="hard") == (
        "B",
        "Hard → cloud",
    )


def test_label_c_pii_wins_over_easy():
    assert label_scenario(force_local=False, has_pii=True, difficulty="easy")[0] == "C"


def test_label_d_force_local_wins():
    letter, note = label_scenario(force_local=True, has_pii=True, difficulty="hard")
    assert letter == "D"
    assert "Force local" in note
