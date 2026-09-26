# Generera fejksäljare och poster

`generate_fake_data.py` används för att fylla en lokal utvecklings- eller testdatabas med exempeldata. Scriptet lägger till nya säljare och poster men raderar inte befintlig data.

## Förutsättningar

Kör scriptet från projektets katalog och i samma virtualenv som applikationen använder. Exempel:

```bash
cd /home/pelle/uaf_auction
source venv/bin/activate
```

Om din virtualenv heter `.venv` använder du i stället:

```bash
source .venv/bin/activate
```

Scriptet använder bland annat `bcrypt`, så virtualenv behöver ha projektets vanliga Python-beroenden installerade.

`config.cfg` måste finnas och innehålla en `DATABASE`-inställning som pekar på den SQLite-databas som ska fyllas med testdata.

## Grundläggande användning

Skapa 10 nya säljare och 100 nya poster:

```bash
python3 generate_fake_data.py --sellers 10 --posts 100
```

Om inga värden anges används standardvärdena 10 säljare och 100 poster:

```bash
python3 generate_fake_data.py
```

Poster fördelas över de nyskapade säljarna och scriptet använder endast godstyper som finns i det aktuella evenemangets `used_types`.

När körningen är klar skrivs de skapade säljarnas id, namn, e-postadress och lösenord ut så att kontona går att använda för manuell testning.

## Parametrar

### `--sellers`

Antal nya säljare som ska skapas.

```bash
python3 generate_fake_data.py --sellers 5 --posts 50
```

Om `--posts` är större än 0 måste minst en ny säljare skapas.

### `--posts`

Antal nya poster som ska skapas och fördelas över de nya säljarna.

```bash
python3 generate_fake_data.py --sellers 3 --posts 30
```

Det går även att bara skapa säljare:

```bash
python3 generate_fake_data.py --sellers 5 --posts 0
```

### `--config`

Använd en annan configfil än `config.cfg`:

```bash
python3 generate_fake_data.py --config config.dev.cfg --sellers 5 --posts 50
```

Databassökvägen läses från `DATABASE` i den angivna configfilen.

### `--seed`

Använd ett bestämt seed-värde när du vill kunna generera samma slumpmässiga följd vid upprepade körningar:

```bash
python3 generate_fake_data.py --sellers 5 --posts 50 --seed 123
```

Observera att databasens befintliga innehåll, autoincrement-id:n och eventuella e-postkollisioner fortfarande kan göra att slutresultatet inte blir byte-för-byte identiskt mellan två databaser.

## Vad scriptet ändrar

Scriptet:

- lägger till nya rader i `sellers` och `posts`,
- behåller all befintlig data,
- skapar lösenord med samma bcrypt-format som applikationen använder,
- använder aktiva godstyper från `used_types`,
- sätter nya poster som ej utskrivna och ej incheckade.

Scriptet tömmer inte databasen och skapar inte ett nytt evenemang.

## Felmeddelanden

Scriptet avbryter utan att generera data om exempelvis:

- `config.cfg` saknas,
- `DATABASE` saknas i configfilen,
- databasfilen inte finns,
- tabellerna `sellers`, `posts` eller `used_types` saknas,
- det inte finns några aktiva godstyper i `used_types`.

## Säkerhet

Verktyget är avsett för lokal utveckling och test. Kontrollera alltid vilken databas `DATABASE` i `config.cfg` pekar på innan du kör scriptet, så att du inte fyller en produktionsdatabas med testdata.
