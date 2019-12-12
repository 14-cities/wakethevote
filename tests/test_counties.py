from wakethevote.counties import find_counties


def test_find_by_county_fips():
    results = list(find_counties("37183"))
    assert len(results) == 1
    assert results[0].name == "Wake"


def test_find_by_county_name():
    results = list(find_counties("Wake"))
    assert len(results) == 1
    assert list(results)[0].fips == "37183"


def test_find_by_county_and_state_name():
    results = list(find_counties("Lee GA"))
    assert len(results) == 1
    assert results[0].fips == "13177"


def test_find_all_by_state_fips():
    for i, county in enumerate(find_counties("37")):
        assert county.state == "NC"
    assert i == 99


def test_find_all_by_state_name():
    for i, county in enumerate(find_counties("NC")):
        assert county.fips[:2] == "37"
    assert i == 99
