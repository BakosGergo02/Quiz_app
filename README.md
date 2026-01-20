# Online vizsgáztató rendszer szakdolgozathoz

### Ingyenesen elérhető verzió: [letsquiz.pythonanywhere.com/](https://letsquiz.pythonanywhere.com/) [![Website letsquiz.pythonanywhere.com](https://img.shields.io/website-up-down-green-red/http/letsquiz.pythonanywhere.com.svg)](http://letsquiz.pythonanywhere.com/)

Saját fejlesztésű online vizsgáztató rendszer, ingyenesen elérhető forráskódból.<br>

[![GitHub license](https://img.shields.io/github/license/akashgiricse/lets-quiz.svg)](https://github.com/akashgiricse/lets-quiz/blob/master/LICENSE)
[![Open Source Love svg1](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/)

## Eredeti (ingyenes) forráskód – rövid összefoglalás

### Az eredeti rendszer egy egyszerű, MCQ-alapú kvízalkalmazás volt:

- kizárólag feleletválasztós kérdések

- egyszerű felhasználókezelés

- minimális admin funkciók

- alap ranglista


## Jelenlegi funkciók (Current Features)

### Oldal- és hozzáféréskezelés

- A kvízek kitöltéséhez bejelentkezés szükséges.

- Regisztráció során a felhasználónak meg kell adnia:

  - felhasználónevet

  - keresztnevet

  - vezetéknevet

  - e-mail címet

  - jelszót

- Bejelentkezéshez elegendő:

  - felhasználónév

  - jelszó

- A rendszer felhasználói csoportokat kezel (pl. Tanár, Diák).

- A kvízekhez felhasználók és/vagy csoportok rendelhetők, így szabályozható, ki töltheti ki az adott kvízt.

- A superuser minden kvízhez hozzáfér.

### Kvíz funkciók

- A rendszer több kérdéstípust támogat:

  - Egyválaszos feleletválasztós kérdés (Single Choice)

  - Többválaszos feleletválasztós kérdés (Multiple Choice)

  - Szöveges válasz megadása

  - Párosító kérdés (drag & drop)

- Egy kvízben több különböző kérdéstípus is szerepelhet.

- Minden kérdés:

  - csak egyszer jelenik meg egy adott kvízkitöltés során

  - a kérdések sorrendje felhasználónként véletlenszerű

- A kvízekhez:

  - időkorlát állítható be (másodpercben)

  - kérdésenkénti azonnali visszajelzés vagy

  - csak a végén megjelenő összesített eredmény választható

- A rendszer támogatja:

  - részpontszámot többválaszos és párosító kérdéseknél

  - kvíz újrakezdését, amely törli az adott kvíz korábbi próbálkozásait

- A kitöltés végén:

  - megjelenik az összpontszám

  - kérdésenként részletes kiértékelés érhető el

### Ranglista funkciók

- A ranglista a felhasználók összesített pontszáma alapján rendezett.

- Holtverseny esetén a korábban regisztrált felhasználó kerül előrébb.

- A ranglista:

  - nyilvánosan elérhető

  - bejelentkezés nélkül is megtekinthető

- A legjobb 3 helyezett kiemelt megjelenítést kap.

### Adminisztrációs és tanári funkciók

- Kvízt létrehozni és szerkeszteni csak tanár vagy admin jogosultsággal lehet.

- Az adminisztrátor / tanár:

  - új kvízt hozhat létre

  - kérdéseket adhat hozzá különböző típusokban

  - meglévő kérdéseket szerkeszthet vagy törölhet

- A kvízekhez:

  - felhasználók

  - felhasználói csoportok rendelhetők hozzá

- A kérdések:

  - sorrendje szabályozott

  - maximális pontszáma egyedileg állítható

- A rendszer automatikusan értékeli a válaszokat:

  - egyválaszos kérdésnél teljes pont / 0 pont

  - többválaszos kérdésnél arányos pontozás

  - párosító kérdésnél részpontszám

- Az admin nem módosíthatja a felhasználók válaszait vagy pontszámait manuálisan.

### Eredmények és visszajelzés

- A felhasználó minden kvíz végén:

  - összesített pontszámot kap

  - részletes, kérdésenkénti kiértékelést lát

- Az egyes kérdéseknél megjelenik:

  - a saját válasz

  - a helyes válasz

  - a kapott pontszám

- Az azonnali visszajelzés esetén a kvíz szünetel, majd a felhasználó manuálisan folytathatja.


## License

MIT License

Copyright (c) 2022 Akash Giri.
