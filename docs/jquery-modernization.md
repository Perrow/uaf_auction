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

De använder i stället `addEventListener`, `fetch`, `async/await` och vanliga DOM-API:er.

## Kvarvarande jQuery-beroenden

De viktigaste kvarvarande jQuery-beroendena är nu tredjepartsberoenden:

- `static/js/jquery.dataTables.min.js`
- `static/js/dataTables.bootstrap.min.js`
- `static/js/bootstrap-show-password.min.js`

`static/js/new_post.js` innehåller äldre jQuery-kod men någon aktiv route eller template som laddar filen har inte hittats i den nuvarande applikationen. Filen behandlas därför som äldre/orphan kod tills motsatsen visas, i stället för som ett aktivt frontendberoende.

## Global laddning

`templates/base.html` laddar fortfarande jQuery globalt. Det är avsiktligt tills DataTables-användningen på listvyerna och `bootstrap-show-password` på användarformulären har moderniserats eller isolerats till endast de sidor som behöver dem.

Bootstrap 5 använder inte jQuery. När de återstående tredjepartsberoendena har hanterats kan jQuery tas bort från `base.html` helt.
