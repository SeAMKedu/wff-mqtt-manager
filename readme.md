[seamk_logo]:       /img/seamk_logo.svg
[epliitto_logo]:    /img/epliitto_logo.jpg
[eakr_eu_logo]:     /img/eakr_eu_logo.jpg

# MQTT vastaanotin

Tämä repository pitää sisällään Pythonilla kirjoitetun palvelun, mikä osaa ottaa vastaan MQTT viestejä, pääsääntöisesti eri IoT-lähteistä, ja tallentaa viestit sopivaan kantaan. Alunperin nämä olivat erillisiä scriptejä, tehty aina tarpeen mukaan, mutta tässä ne on refactoroitu yhden frameworkin alle, mahdollistaen suht helpon lisäyksen tuleville viesteille. 

Ohjelma itsessään ei vielä paljoa tee, sinulla pitää olla pääsy MQTT brokeriin, josta viestejä kuunnellaan sekä InfluxDB ja/tai MongoDB kanta, minne viestejä tallentaa. Tässä ei oteta kantaa niiden asentamiseen. 

## Luo ajoympäristö

Alla oleva luo python virtuaaliympäristön, aktivoi sen ja asentaa tarvittavat kirjastot.

```
python -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel
pip install --upgrade -r requirements.txt
```

## Muokkaa ini-tiedosto

`sample.ini` tiedosto on esimerkki asetuksista. Ota se pohjaksi ja valitse tarvittavat tiedot tietokantayhteyksien luontia varten ja täytä asetukset niille handlereille, joita olet käyttämässä. 

### Influxdb

InfluxDB tarvitsee API urlin, access tokenin ja organisaation, jonka alle tiedot kerätään. Bucketit määritellään handlereissä.

```
[INFLUXDB]
InfluxDBHost = http://localhost:8086
Token = INFLUXDB_TOKEN
Org = ORG
```

### MongoDb

MongoDB yhteys on käyttäjätunnuksen ja salasanan kautta. Näistä handlereistä vain punnitukset tallentuvat Mongoon.

```
[MONGODB]
Hostname = localhost
Username = USERNAME
Password = PASSWORD
AuthenticationDatabase = AUTHDB
Database = DATABASE
AuthMechanism = AUTH_MECHANISM
```

### RuuviHandler

RuuviGateway kautta tulevien viestin hallinta. Kerro mitä mqtt topicia seurataan ja minne bucketiin data tallennetaan. Tämä osaa poimia ruuvitagien lisäksi, myös Tilt Hydrometrien iBeacon viestit.

`ALLOWED_MACS` kohdassa voit listata ne tagit, joiden tiedot on tarkoitus kerätä. RuuviGateway lähettää kaikki BLE viestit mitä se näkee eteenpäin, joten ohikulkevasta laitteesta voi tulla viestejä, joita ei tarvitse tallentaa. 

```
[RUUVIGATEWAY]
Topic = topic/for/ruuvigw/messages/#
Bucket = BUCKET

[RUUVIGATEWAY.ALLOWED_MACS]
uuid01   = "0123456789ab" # sensor 1
uuid02   = "fedcba987654" # sensor 2
```

### RuuviVibraHandler

Tämä käsittelijä on RuuviTageille, joihin on päivitetty tärinän analysointia varten oma firmwarensa. 

```
[RUUVIVIBRA]
Topic = topic/for/ruuvigw/vibrafw/messages/#
Bucket = BUCKET

[RUUVIVIBRA.ALLOWED_MACS]
mac01 = { "mac": "aabbccddeeff", "name": "vibra 1", "seen": false }
mac02 = { "mac": "ffeeddccbbaa", "name": "vibra 2", "seen": false }
```

### ShellyHandler

Shelly käsittelijä odottaa viestejä Shelly Pro 3EM energiamittarista.

```
[SHELLY3EM]
Topic = topic/for/shelly/energy/messages/#
Bucket = BUCKET
Location = METER_LOCATION
```

### HomogenizerHandler

Homogenisaattorin kyljessä oleva ESP32 lähettää paineanturitietoja myös MQTT brokerille.

```
[HOMOGENIZER]
Topic = topic/for/homogenizer/messages/#
Bucket = BUCKET
```

### BalanceHandler

PC:llä pyöritettävä python scripti lukee sarjaportin kautta Radwag vaa'oista tulevia punnituksia ja lähettää tiedon eteenpäin. Tämä käsittelijä tallentaa nämä mittaukset MongoDB:hen.

```
[BALANCE]
Topic = topic/for/balance/messages/#
Collection = MONGO_COLLECTION
```

### MQTTStatsHandler

MQTTStatsHandler kerää statistiikka tietoa MQTT brokerin käytöstä ja tallentaa ne InfluxDB:hen.

```
[MQTT_STATS]
Topic = $SYS/broker/#
Bucket = BUCKET
```

## Asenna service

Jotta palvelu käynnistyisi helposti palvelimen kanssa, Ubuntun kanssa voit ottaa `sample.service` tiedosto pohjaksi ja päivittää polut oikeiksi sekä kertoa mitä .ini tiedostoa tulisi käyttää. Enabloi .service tiedosto ja käynnistä palvelu. 

```
$ sudo systemctl enable absolute/path/to/file.service
$ sudo systemctl start file.service
$ sudo systemctl status file.service
```

## Wise Frami Food hanke

Tämä ohjelma luotiin osana Wise Frami Food hanketta, jossa rakennettiin piloitointiympäristö Frami Food Labin yhteyteen. s

![eakr_eu_logo] 

---

![epliitto_logo]

---

![seamk_logo]
