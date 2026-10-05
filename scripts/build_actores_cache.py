import json
import os
import time
import urllib.request
import urllib.parse
import unicodedata

def normalizar_texto(texto):
    if not texto:
        return ""
    texto = texto.lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

CACHE_FILE = os.path.join(os.path.dirname(__file__), "actores_cache.json")
if not os.path.exists(CACHE_FILE):
    # Try current dir or parent
    if os.path.exists("actores_cache.json"):
        CACHE_FILE = "actores_cache.json"

FILM_KEYWORDS = [
    "actor", "actress", "actriz", "filmmaker", "director", "cineasta", "guionista",
    "producer", "productor", "film", "película", "pelicula", "cinema", "cine"
]

def find_actor_films(name):
    # Step 1: Find entity ID via wbsearchentities
    url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(name)}&language=es&format=json&limit=3"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 TVBoxCatalog/2.0 (contact: admin@tvbox.lan)'})
    
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        results = data.get('search', [])
        
    if not results:
        return None, []
        
    chosen_qid = None
    chosen_label = None
    for r in results:
        desc = (r.get('description', '') or '').lower()
        if any(k in desc for k in FILM_KEYWORDS):
            chosen_qid = r.get('id')
            chosen_label = r.get('label')
            break
            
    if not chosen_qid:
        chosen_qid = results[0].get('id')
        chosen_label = results[0].get('label')
        
    # Step 2: Fetch films by QID directly in SPARQL
    sparql = f"""
    SELECT DISTINCT ?film ?tmdbId WHERE {{
      {{ ?film wdt:P161 wd:{chosen_qid} }} UNION {{ ?film wdt:P57 wd:{chosen_qid} }}
      ?film wdt:P4947 ?tmdbId .
    }}
    LIMIT 200
    """
    sparql_url = 'https://query.wikidata.org/sparql?' + urllib.parse.urlencode({'query': sparql, 'format': 'json'})
    sparql_req = urllib.request.Request(sparql_url, headers={'User-Agent': 'Mozilla/5.0 TVBoxCatalog/2.0 (contact: admin@tvbox.lan)'})
    
    with urllib.request.urlopen(sparql_req, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        bindings = data.get('results', {}).get('bindings', [])
        tmdb_ids = set()
        for b in bindings:
            tid = b.get('tmdbId', {}).get('value')
            if tid:
                try:
                    tmdb_ids.add(int(tid))
                except ValueError:
                    pass
                    
    return chosen_label, sorted(list(tmdb_ids))

SEED_PEOPLE = [
    # Top Hollywood Actors
    ("Christian Bale", ["bale"]),
    ("Leonardo DiCaprio", ["dicaprio"]),
    ("Brad Pitt", ["pitt"]),
    ("Tom Cruise", ["cruise"]),
    ("Keanu Reeves", ["reeves"]),
    ("Johnny Depp", ["depp"]),
    ("Robert De Niro", ["de niro"]),
    ("Al Pacino", ["pacino"]),
    ("Morgan Freeman", ["freeman"]),
    ("Denzel Washington", []),
    ("Tom Hanks", ["hanks"]),
    ("Will Smith", []),
    ("Jim Carrey", ["carrey"]),
    ("Robin Williams", []),
    ("Harrison Ford", []),
    ("Samuel L. Jackson", ["samuel jackson"]),
    ("Matt Damon", ["damon"]),
    ("Ben Affleck", ["affleck"]),
    ("George Clooney", ["clooney"]),
    ("Russell Crowe", ["crowe"]),
    ("Mel Gibson", ["gibson"]),
    ("Liam Neeson", ["neeson"]),
    ("Nicolas Cage", ["cage"]),
    ("Bruce Willis", ["willis"]),
    ("John Travolta", ["travolta"]),
    ("Anthony Hopkins", ["hopkins"]),
    ("Clint Eastwood", ["eastwood"]),
    ("Sylvester Stallone", ["stallone"]),
    ("Arnold Schwarzenegger", ["schwarzenegger"]),
    ("Jason Statham", ["statham"]),
    ("Vin Diesel", ["diesel"]),
    ("Dwayne Johnson", ["the rock"]),
    ("Ryan Reynolds", []),
    ("Chris Hemsworth", ["hemsworth"]),
    ("Chris Evans", []),
    ("Robert Downey Jr.", ["downey jr", "robert downey"]),
    ("Mark Ruffalo", ["ruffalo"]),
    ("Scarlett Johansson", ["johansson"]),
    ("Emma Stone", []),
    ("Margot Robbie", ["robbie"]),
    ("Pedro Pascal", ["pascal"]),
    ("Cillian Murphy", ["murphy"]),
    ("Joaquin Phoenix", ["phoenix"]),
    ("Javier Bardem", ["bardem"]),
    ("Antonio Banderas", ["banderas"]),
    ("Penélope Cruz", ["penelope cruz"]),
    ("Salma Hayek", ["hayek"]),
    ("Benicio del Toro", ["benicio"]),
    ("Jackie Chan", []),
    ("Bruce Lee", []),
    ("Jet Li", []),
    ("Adam Sandler", ["sandler"]),
    ("Ben Stiller", ["stiller"]),
    ("Steve Carell", ["carell"]),
    ("Owen Wilson", []),
    ("Jack Black", []),
    ("Eddie Murphy", []),
    ("Matthew McConaughey", ["mcconaughey"]),
    ("Woody Harrelson", ["harrelson"]),
    ("Gary Oldman", ["oldman"]),
    
    # Argentine / Latin American Cinema
    ("Ricardo Darín", ["darin", "ricardo darin"]),
    ("Guillermo Francella", ["francella"]),
    ("Diego Peretti", ["peretti"]),
    ("Rodrigo de la Serna", ["de la serna"]),
    ("Leonardo Sbaraglia", ["sbaraglia"]),
    ("Luis Brandoni", ["brandoni"]),
    ("Oscar Martínez", ["oscar martinez"]),
    ("Norma Aleandro", ["aleandro"]),
    ("Federico Luppi", ["luppi"]),
    ("Mercedes Morán", ["mercedes moran"]),
    ("Gael García Bernal", ["gael garcia"]),
    ("Diego Luna", []),
    ("Wagner Moura", ["moura"]),
    
    # Top Directors
    ("Christopher Nolan", ["nolan"]),
    ("Quentin Tarantino", ["tarantino"]),
    ("Martin Scorsese", ["scorsese"]),
    ("Steven Spielberg", ["spielberg"]),
    ("James Cameron", ["cameron"]),
    ("Guillermo del Toro", ["del toro"]),
    ("Denis Villeneuve", ["villeneuve"]),
    ("David Fincher", ["fincher"]),
    ("Ridley Scott", []),
    ("Stanley Kubrick", ["kubrick"]),
    ("Alfred Hitchcock", ["hitchcock"]),
    ("Francis Ford Coppola", ["coppola"]),
    ("George Lucas", []),
    ("Peter Jackson", []),
    ("Tim Burton", ["burton"]),
    ("Guy Ritchie", ["ritchie"]),
    ("Wes Anderson", []),
    ("Alejandro González Iñárritu", ["inarritu"]),
    ("Alfonso Cuarón", ["cuaron"]),
    ("Pedro Almodóvar", ["almodovar"]),
    ("Juan José Campanella", ["campanella"]),
    ("Damián Szifron", ["szifron"]),
    ("David Lynch", ["lynch"]),
    ("Bong Joon-ho", ["bong joon ho"]),
    ("Hayao Miyazaki", ["miyazaki"])
]

def main():
    cache_path = "actores_cache.json"
    cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
            print(f"Loaded existing cache with {len(cache)} keys.")
        except Exception as e:
            print(f"Error loading cache: {e}")

    saved_count = 0
    for name, aliases in SEED_PEOPLE:
        norm_name = normalizar_texto(name)
        if norm_name in cache and len(cache[norm_name]) > 0:
            # Check if aliases need populating
            for alias in aliases:
                norm_alias = normalizar_texto(alias)
                if norm_alias not in cache:
                    cache[norm_alias] = cache[norm_name]
            continue

        print(f"Fetching {name}...")
        try:
            label, tmdb_ids = find_actor_films(name)
            if tmdb_ids:
                print(f" -> Found {len(tmdb_ids)} films for {label} ({name})")
                cache[norm_name] = tmdb_ids
                for alias in aliases:
                    cache[normalizar_texto(alias)] = tmdb_ids
                saved_count += 1
            else:
                print(f" -> No films found for {name}")
                cache[norm_name] = []
        except Exception as e:
            print(f" -> Error fetching {name}: {e}")

        time.sleep(0.4)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"\nDone! Saved {saved_count} new people. Total cached keys: {len(cache)}.")

if __name__ == "__main__":
    main()
