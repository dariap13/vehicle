from app.classifier.vehicle_classifier import map_imagenet_label


def test_map_motorcycle_label():
    vehicle_type, is_vehicle = map_imagenet_label("moped")

    assert vehicle_type == "motocykl"
    assert is_vehicle is True


def test_map_non_vehicle_label():
    vehicle_type, is_vehicle = map_imagenet_label("golden retriever")

    assert vehicle_type == "inne"
    assert is_vehicle is False
