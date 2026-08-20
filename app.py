from flask import Flask, jsonify, request
import mysql.connector
import os

app = Flask(__name__)


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "mariadb"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "socialdb"),
        user=os.getenv("DB_USER", "socialuser"),
        password=os.getenv("DB_PASSWORD", "SocialPass123")
    )


@app.route("/")
def home():
    return jsonify({
        "service": "reaction-service",
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route("/db-test")
def db_test():
    try:
        connection = get_db_connection()

        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        return jsonify({
            "status": "connected",
            "database": result[0]
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/reactions", methods=["GET"])
def get_reactions():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, user_id, post_id, reaction, created_at
            FROM reactions
            ORDER BY id
        """)

        reactions = cursor.fetchall()

        cursor.close()
        connection.close()

        return jsonify(reactions)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/reactions/<int:post_id>", methods=["GET"])
def get_post_reactions(post_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, user_id, post_id, reaction, created_at
            FROM reactions
            WHERE post_id = %s
            ORDER BY id
        """, (post_id,))

        reactions = cursor.fetchall()

        cursor.close()
        connection.close()

        return jsonify(reactions)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/reactions", methods=["POST"])
def create_reaction():
    data = request.get_json()

    user_id = data.get("user_id")
    post_id = data.get("post_id")
    reaction = data.get("reaction")

    if not user_id or not post_id or not reaction:
        return jsonify({
            "status": "error",
            "message": "user_id, post_id and reaction are required"
        }), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO reactions (user_id, post_id, reaction)
            VALUES (%s, %s, %s)
        """, (user_id, post_id, reaction))

        connection.commit()

        reaction_id = cursor.lastrowid

        cursor.close()
        connection.close()

        return jsonify({
            "status": "created",
            "id": reaction_id
        }), 201

    except mysql.connector.IntegrityError:
        return jsonify({
            "status": "error",
            "message": "User already reacted to this post"
        }), 409

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/reactions/<int:reaction_id>", methods=["DELETE"])
def delete_reaction(reaction_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM reactions WHERE id = %s",
            (reaction_id,)
        )

        connection.commit()

        if cursor.rowcount == 0:
            cursor.close()
            connection.close()

            return jsonify({
                "status": "error",
                "message": "Reaction not found"
            }), 404

        cursor.close()
        connection.close()

        return jsonify({
            "status": "deleted",
            "id": reaction_id
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
