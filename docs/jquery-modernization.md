# jQuery-modernisering

## Migrerat till modern JavaScript

Följande aktiva sidunika script använder inte längre jQuery:

- `static/js/auktion.js`
- `static/js/create_event.js`
- `static/js/flea_market.js`
- `static/js/display_one.js`
- `static/js/display_two.js`
- `static/js/edit_post.js`
- `static/js/register_many.js`
- `static/js/sort_tables.js`
- `static/js/password_toggle.js`

De använder i stället `addEventListener`, `fetch`, `async/await` och vanliga DOM-API:er.

## Global laddning

`templates/base.html` laddar inte längre jQuery, DataTables eller `bootstrap-show-password` globalt.

Listvyerna använder nu en liten jQuery-fri sorteringsfunktion och lösenordsfält använder en egen jQuery-fri Visa/Dölj-funktion.

## Kvarvarande äldre filer

Följande filer finns fortfarande i `static/js`, men behövs inte längre av de moderniserade aktiva flödena:

- `static/js/jquery-3.1.1.min.js`
- `static/js/jquery.dataTables.min.js`
- `static/js/dataTables.bootstrap.min.js`
- `static/js/bootstrap-show-password.min.js`
- `static/js/new_post.js`

`new_post.js` innehåller äldre jQuery-kod men någon aktiv route eller template som laddar filen har inte hittats. Filerna kan tas bort i ett separat städärende när övriga kvarvarande templates har verifierats.
