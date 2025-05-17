import json
from flask import Flask, request, jsonify, render_template_string
import os

app = Flask(__name__)

REACTIONS_FILE = "github_reactions.json"
REACTION_TYPES = ["👍", "❤️", "😮"]  # 👍 = Like, ❤️ = Love, 😮 = Wow

def load_reactions():
    if not os.path.exists(REACTIONS_FILE):
        return {reaction: [] for reaction in REACTION_TYPES}
    with open(REACTIONS_FILE, "r") as f:
        data = json.load(f)
    for reaction in REACTION_TYPES:
        if reaction not in data:
            data[reaction] = []
    return data

def save_reactions(data):
    with open(REACTIONS_FILE, "w") as f:
        json.dump(data, f)

@app.route("/")
def index():
    reactions = load_reactions()
    user = request.args.get("user", "anonymous")
    html = """
    <style>
    #reactions {
        display: flex;
        gap: 16px;
        margin: 24px 0;
        justify-content: center;
    }
    .reaction-btn {
        background: #fff;
        border: none;
        border-radius: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        padding: 12px 20px;
        font-size: 1.7rem;
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        transition: box-shadow 0.2s, background 0.2s;
        outline: none;
    }
    .reaction-btn:disabled {
        background: #e0e0e0;
        color: #aaa;
        cursor: not-allowed;
        box-shadow: none;
    }
    .reaction-btn:not(:disabled):hover {
        background: #f0f0f0;
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    }
    .reaction-count {
        font-size: 1.1rem;
        color: #555;
        margin-left: 4px;
        min-width: 18px;
        text-align: center;
    }
    </style>
    <h2 style="text-align:center;">React to this GitHub profile!</h2>
    <div id="reactions">
    {% for reaction in reactions %}
        <button onclick="sendReaction('{{reaction}}')" class="reaction-btn" id="btn-{{reaction}}" {% if user in reactions[reaction] %}disabled{% endif %}>
            {{reaction}} <span class="reaction-count" id="count-{{reaction}}">{{reactions[reaction]|length}}</span>
        </button>
    {% endfor %}
    </div>
    <script>
    function sendReaction(reaction) {
        fetch('/react', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({reaction: reaction, user: "{{user}}"})
        }).then(r => r.json()).then(data => {
            if (data.success) {
                // Reload all buttons and counts after a reaction
                fetch(window.location.href)
                    .then(resp => resp.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        const newReactions = doc.getElementById('reactions');
                        document.getElementById('reactions').innerHTML = newReactions.innerHTML;
                    });
            }
        });
    }
    </script>
    """
    return render_template_string(html, reactions=reactions, user=user)

@app.route("/react", methods=["POST"])
def react():
    data = request.get_json()
    reaction = data.get("reaction")
    user = data.get("user")
    if reaction not in REACTION_TYPES or not user:
        return jsonify(success=False), 400
    reactions = load_reactions()
    # Remove user from all reactions before adding to new one
    for r in REACTION_TYPES:
        if user in reactions.get(r, []):
            reactions[r].remove(user)
    if reaction not in reactions:
        reactions[reaction] = []
    reactions[reaction].append(user)
    save_reactions(reactions)
    return jsonify(success=True, count=len(reactions[reaction]))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)