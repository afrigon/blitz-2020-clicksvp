from bot import flood_fill


def test_flood_fill_closed():
    points = [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 1), (1, 1)]
    actual = flood_fill(points)
    assert actual == set(points)


def test_flood_fill_open():
    points = [
        (0, 0),
        (0, 1),
        (0, 2),
        (0, 3),
        (1, 0),
        (2, 0),
        (2, 1),
        (3, 1),
        (3, 2),
        (3, 3),
        (2, 3),
        (1, 3),
    ]
    filled_points = [(1, 1), (1, 2), (2, 2)]
    expected_points = set(points + filled_points)
    assert flood_fill(points) == expected_points


def test_flood_fill_more():
    points = [
        (0, 1),
        (0, 2),
        (0, 3),
        (0, 4),
        (0, 5),
        (0, 6),
        (1, 0),
        (1, 6),
        (2, 0),
        (2, 1),
        (2, 2),
        (2, 3),
        (2, 4),
        (2, 5),
        (2, 6),
        (3, 1),
        (3, 2),
        (3, 5),
    ]
    filled_points = [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5)]
    expected_points = set(points + filled_points)
    assert flood_fill(points) == expected_points
