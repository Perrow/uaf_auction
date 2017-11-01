# coding=utf-8
__author__ = 'kristian'

import random
import time

class Faker:

    def __init__(self):
        """
        Generates data to insert into the database
        """
        self.fish_names = [
            [u"Ancistrus sp.", u"skäggmunsmal"],
            [u"Mikrogeophagus ramirezi", u"Fjärilsciklid"],
            [u"Pterophyllum scalare", u"Skalar"],
            [u"Betta splendens", u"Kampfisk"],
            [u"Poecilia reticulata", u"Guppy"],
            [u"Xiphophorus maculatus", u"Platy"],
            [u"Paracheirodon axelrodi", u"Kardinaltetra"],
            [u"Carassius auratus auratus", u"Guldfisk"],
            [u"Crossocheilus oblongus", u"Siamesisk algätare, algätare"],
            [u"Paracheirodon innesi", u"Neontetra"],
            [u"Glyptoperichthys gibbiceps", u"Segelfenspleco"],
            [u"Apistogramma cacatuoides", u"Kakadua ciklid"],
            [u"Labidochromis caeruleus", u"Golden labidochromis"],
            [u"Pelvicachromis pulcher", u"Palettciklid"],
            [u"Chromobotia macracanthus", u"Praktbotia"],
            [u"Poecilia sphenops", u"Blackmolly"],
            [u"Trichogaster lalius", u"Dvärggurami"],
            [u"Otocinclus vittatus", u"Randig otocinclus"],
            [u"Metriaclima estherae", u"Rödzebra"],
            [u"Hasemania nana", u"Koppartetra"],
            [u"Balantiocheilus melanopterus", u"Silverhaj"],
            [u"Xiphophorus helleri", u"Svärdbärare"],
            [u"", u""]
        ]

        self.plant_names = [
            [u"", u"Aponogeton rigidifolius"],
            [u"Hornsärv", u"Ceratophyllum demersum"],
            [u"Cryptocoryne", u"Cryptocoryne wendtii 'brown'"],
            [u"Dvärganubias", u"Anubias barteri var. nana"],
            [u"Svärdsplanta", u"Echinodorus 'Ozelot'"],
            [u"", u"Hygrophila difformis"],
            [u"Ciklidgräs", u"Ophiopogon japonicus"],
            [u"", u"Rotala rotundifolia"],
            [u"", u""]
        ]

        self.shrimp_names = [
            [u"Körsbärsräka", u"Neocaridina davidi var. red"],
            [u"Gul Körsbärsräka", u"Neocaridina davidi var. yellow"],
            [u"Röd Riliräka", u"Neocaridina davidi var. Röd Rili"],
            [u"Rödsakura Räka", u"Neocaridina davidi var. Red sakura"],
            [u"Zebraräka", u"Caridina cf. babaulti ssp. Indian zebra"],
            [u"Crystal red räka", u"Caridina cf. cantonensis ”Crystal Red”"]
        ]

        # Most common surnamnes 2016
        self.surnames = [
            u"Andersson",
            u"Karlsson",
            u"Johansson",
            u"Karlsson",
            u"Nilsson",
            u"Eriksson",
            u"Larsson",
            u"Olsson",
            u"Persson",
            u"Svensson",
            u"Gustafsson"
        ]

        # Most common first names in order 2016
        self.first_names = [
            u"Anna",
            u"Lars",
            u"Eva",
            u"Maria",
            u"Mikael",
            u"Anders",
            u"Johan",
            u"Karin",
            u"Per",
            u"Erik",
            u"Karl",
            u"Peter",
            u"Jan",
            u"Thomas",
            u"Kristina",
            u"Lena",
            u"Sara",
            u"Kerstin",
            u"Emma",
            u"Ingrid"
        ]

        # Most common street names in Sweden
        self.street_names = [ 
            u"Ringvägen",
            u"Storgatan",
            u"Skolgatan",
            u"Järnvägsgatan",
            u"Skogsvägen",
            u"Villavägen"
        ]

        # Largest cities in Sweden
        self.cities = [
            [u"Stockholm", u"16"],
            [u"Göteborg", u"41"],
            [u"Malmö", u"21"],
            [u"Uppsala", u"75"],
            [u"Västerås", u"72"],
            [u"Örebro", u"70"],
            [u"Linköping", u"58"],
            [u"Helsingborg", u"25"],
            [u"Jönköping", u"55"],
            [u"Norrköping", u"60"],
            [u"Umeå", u"90"],
            [u"Gävle", u"80"],
            [u"Borås", u"50"],
            [u"Eskilstuna", u"63"],
            [u"Södertälje", u"15"],
            [u"Karlstad", u"65"],
            [u"Täby", u"18"],
            [u"Växjö", u"35"],
            [u"Halmstad", u"30"]
        ]
        # Most common passwords 2016
        self.passwords = [
            u"123456",
            u"password",
            u"12345",
            u"12345678",
            u"football",
            u"qwerty",
            u"1234567890",
            u"1234567",
            u"princess",
        ]

        self.aquarium_clubs = [
            u"Västra Aros Akvarieförening",
            u"Uppsala Akvarieförening",
            u"Spånga Akvarieförening",
            u"Haninge Akvarieförening",
            u"Bollmora Akvarieklubb",
            u"Carlskrona Akvarieförening",
            u"Linköpings akvarieförening",
            u"Malmö Akvarieförening",
            u"Stockholms akvarieförening",
            u"Örebro Akvarieklubb",
            u"Umeå Akvarieförening"
        ]

    def get_seller_name_and_email(self):
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.surnames)
        name = "{} {}".format(first_name, last_name)
        email = "{}.{}@mail.com".format(first_name, last_name).lower()
        return name, email
    
    def get_address(self):
        city, zip_base = random.choice(self.cities)
        street = random.choice(self.street_names)
        zip_code = u"{}{} {}{}".format(zip_base, random.randint(0, 9), random.randint(0, 9), random.randint(0, 9))
        street_number = random.randint(1, 100)
        address = u"{} {}, {} {}".format(street, street_number, zip_code, city)
        return (address)

    def get_phone(self):
        phone_number = "0"
        for n in range(9):
            if n == 3:
                phone_number += "-"
            phone_number += str(random.randint(0, 9))
        return phone_number

    def get_password(self):
        return random.choice(self.passwords)
        # return u"password"

    def get_aquarium_club(self):
        return random.choice(self.aquarium_clubs)

    def generate_seller(self, admin="no"):
        name, email = self.get_seller_name_and_email()
        address = self.get_address()
        phone_number = self.get_phone()
        password = self.get_password()
        club = self.get_aquarium_club()
        return name, address, email, phone_number, club, admin, password, time.strftime("%Y-%m-%d %H:%M:%S"), "yes", "yes"

    def get_fish_name(self):
        return random.choice(self.fish_names)

    def get_plant_name(self):
        return random.choice(self.plant_names)

    def get_shrimp_name(self):
         return random.choice(self.shrimp_names)

    def generate_fish_auction_post(self, seller_id):
        type = 1
        comment = ""
        sci_name, pop_name = self.get_fish_name()
        return seller_id, sci_name, pop_name, comment, type, time.strftime("%Y-%m-%d %H:%M:%S"), None, "no"

    def generate_plant_fleamarket_post(self, seller_id):
        type = 8
        comment = ""
        pop_name, sci_name = self.get_plant_name()
        return seller_id, sci_name, pop_name, comment, type, time.strftime("%Y-%m-%d %H:%M:%S"), random.randint(1, 10) * 10, "no"

    def generate_shrimp_fleamarket_post(self, seller_id):
        type = 4
        comment = ""
        pop_name, sci_name = self.get_shrimp_name()
        return seller_id, sci_name, pop_name, comment, type, time.strftime("%Y-%m-%d %H:%M:%S"), random.randint(1, 10) * 10, "no"

if __name__ == "__main__":
    
    F = Faker()
    # print(F.get_fish_name())
    print(F.get_seller_name_and_email())
    print(F.get_address())
    print(F.get_phone())
    print(F.generate_fish_auction_post(3))

