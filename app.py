from flask import Flask, render_template, request, session, redirect, url_for
import json, random

app = Flask(__name__, subdomain_matching=True)
app.config["SERVER_NAME"] = "domain.local:5000"
app.secret_key = "testsecret123"

ATTRIBUTE_ORDER = [
    "Type",
    "Ability",
    "BST",
    "Stages",
    "Habitat",
    "Generation",
]

TYPE_COLORS = {
    "fire": "#F08030",
    "water": "#6890F0",
    "grass": "#78C850",
    "electric": "#F8D030",
    "psychic": "#F85888",
    "ice": "#98D8D8",
    "dragon": "#7038F8",
    "dark": "#1E150F",
    "fairy": "#EE99AC",
    "normal": "#A8A878",
    "fighting": "#C03028",
    "flying": "#A890F0",
    "poison": "#A040A0",
    "ground": "#E0C068",
    "rock": "#B8A038",
    "bug": "#A8B820",
    "ghost": "#705898",
    "steel": "#B8B8D0",
}


# ---------- LOAD DATA ----------
def load_pokemon(path="pkmn.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

pokemon = load_pokemon()
pokemon_by_name = {p["name"].lower(): p for p in pokemon}

# ---------- HELPERS ----------
def normalize(name):
    return name.strip().lower()
# --------------------------------------------------
def base_species_name(name: str) -> str:
    return name.split("-")[0].lower()
# --------------------------------------------------
def compare_lists(guess, target):
    g, t = set(guess), set(target)
    if g == t:
        return "green"
    elif g & t:
        return "yellow"
    return "red"
# --------------------------------------------------
def compare_number(guess, target):
    if guess == target:
        return "green"
    elif abs(guess - target) <= 50:
        return "yellow"
    elif abs(guess - target) <= 100:
        return "orange"
    return "red"
# --------------------------------------------------
def compare_value(guess, target):
    return "green" if guess == target else "red"
# --------------------------------------------------
def evaluate_guess(guess, target):
    return {
        "Type": (compare_lists(guess["types"], target["types"]), " / ".join(guess["types"])),
        "Ability": (compare_lists(guess["abilities"], target["abilities"]), " / ".join(guess["abilities"])),
        "BST": (compare_number(guess["bst"], target["bst"]), guess["bst"]),
        "Stages": (compare_value(guess["evo-stages"], target["evo-stages"]), guess["evo-stages"]),
        "Habitat": (compare_lists(guess["habitats"], target["habitats"]), " + ".join(guess["habitats"])),
        "Generation": (compare_value(guess["generation"], target["generation"]), guess["generation"]),
    }

# ---------- ROUTES ----------
@app.route("/", methods=["GET", "POST"], subdomain="wordlemon")
def wordlemon():
    # Reset the game if session does not have a target (fresh start or script restart)
    # Always start fresh if no game exists
    if "target" not in session:
        session.clear()  # clears all session data
        session["target"] = random.choice(pokemon)["name"]
        session["guessed_species"] = []
        session["guesses"] = []


    message = None
    guess_count = len(session.get("guesses", []))
    MAX_GUESSES = 8

    if request.method == "POST":
        name = normalize(request.form["guess"])

        if name not in pokemon_by_name:
            message = "Invalid Pokémon name."
        else:
            guess = pokemon_by_name[name]

            # Resolve base species names
            guess_species = base_species_name(guess["name"])
            target_species = base_species_name(session["target"])

            # Check if species already guessed (wrong)
            if guess_species in session.get("guessed_species", []):
                message = f"You already guessed {guess_species.capitalize()}."
            else:
                # Use base species for stat comparison
                guess_for_compare = pokemon_by_name.get(guess_species, guess)
                target_for_compare = pokemon_by_name.get(target_species, pokemon_by_name[normalize(session["target"])])

                result = evaluate_guess(guess_for_compare, target_for_compare)

                # Win check (species match)
                if guess_species == target_species:
                    finished_target = session["target"]

                    message = f"🎉 You win!"
                    session["finished_target"] = finished_target

                    session.pop("target", None)
                    session.pop("guesses", None)
                    session.pop("guessed_species", None)

                else:
                    # Wrong guess → store species and results
                    guessed_species = session.get("guessed_species", [])
                    guessed_species.append(guess_species)
                    session["guessed_species"] = guessed_species

                    guesses = session.get("guesses", [])
                    guesses.insert(0, (guess["name"], result, guess["types"]))  # keep full form name for display
                    session["guesses"] = guesses

                    guess_count = len(session["guesses"])
                    if guess_count >= MAX_GUESSES:
                        finished_target = session["target"]

                        message = "Game over! Correct Pokémon:"
                        session["finished_target"] = finished_target

                        session.pop("target", None)
                        session.pop("guesses", None)
                        session.pop("guessed_species", None)


    all_pokemon_names = sorted([p["name"] for p in pokemon])
    if session.get("finished_target"):
        target_name = session["finished_target"].lower()
        target = pokemon_by_name[target_name]

        # Compare against itself so everything is green
    finished_card = None

    finished_target = session.get("finished_target")

    if finished_target:
        target = pokemon_by_name[finished_target.lower()]
        finished_card = (
            target["name"],
            evaluate_guess(target, target),  # self compare = all green
            target["types"]                   # <-- add types here
        )


    return render_template(
        "wordlemon.html",
        guesses=session.get("guesses", []),
        attribute_order=ATTRIBUTE_ORDER,
        guess_count=len(session.get("guesses", [])),
        message=message,
        max_guesses=MAX_GUESSES,
        all_pokemon_names=all_pokemon_names,
        finished_target=session.get("finished_target"),
        finished_card=finished_card,
        type_colors=TYPE_COLORS
    )
# --------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    session.clear()
    return render_template(
        "index.html"
    )

@app.route("/home", subdomain="wordlemon")
def home():
    session.clear()
    return redirect(url_for("index", _external=True))


if __name__ == "__main__":
    app.run(debug=True)
