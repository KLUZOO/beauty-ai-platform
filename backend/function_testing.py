from services.places_service import PlacesService

if __name__ == "__main__":
    place_service = PlacesService("Київ")

    for place in place_service.find_places():
        print(place)
