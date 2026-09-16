# jQuery-modernisering

## Migrerat till modern JavaScript

Följande sidunika script använder inte längre jQuery:

- `static/js/auktion.js` – använder nu `addEventListener`, `fetch`, `async/await` och vanliga DOM-API:er.
- `static/js/create_event.js` – använder nu `addEventListener`, `querySelectorAll` och vanliga DOM-API:er.

## Kvarvarande verifierade jQuery-beroenden

Följande egna script använder fortfarande jQuery och bör migreras stegvis i senare arbete:

- `static/js/flea_market.js`
- `static/js/display_one.js`
- `static/js/display_two.js`
- `static/js/edit_post.js`
- `static/js/new_post.js`
- `static/js/register_many.js`

Dessutom finns tredjepartsberoenden som bygger på jQuery:

- `static/js/jquery.dataTables.min.js`
- `static/js/dataTables.bootstrap.min.js`
- `static/js/bootstrap-show-password.min.js`

## Global laddning

`templates/base.html` laddar fortfarande jQuery globalt. Det är avsiktligt tills de kvarvarande äldre sidorna och tredjepartsberoendena ovan har flyttats eller ersatts. Bootstrap 5 använder däremot inte jQuery; Bootstrap laddas via `bootstrap.bundle.min.js` separat.

När de återstående sidunika beroendena har migrerats bör jQuery och jQuery-baserade plugins flyttas från `base.html` till endast de templates som fortfarande behöver dem, och därefter tas bort helt när inga beroenden återstår.
