from flask import Flask, jsonify, render_template, request
import pandas as pd

app = Flask(__name__)

# =====================
# CSV 読み込み
# =====================

# movies（パイプ区切り）
movies = pd.read_csv(
    "data/movies_100k.csv",
    sep="|",
    encoding="latin-1"
)

# ratings（カンマ区切り・ヘッダーあり）
ratings = pd.read_csv(
    "data/ratings_100k.csv"
)

# =====================
# 列名を統一（ここが超重要）
# =====================

ratings = ratings.rename(columns={
    "userId": "user_id",
    "movieId": "movie_id"
})

# 型を統一（NaN対策込み）
movies["movie_id"] = movies["movie_id"].astype(int)

ratings = ratings.dropna(subset=["movie_id", "rating"])
ratings["movie_id"] = ratings["movie_id"].astype(int)
ratings["rating"] = ratings["rating"].astype(float)

# =====================
# 画面
# =====================

@app.route("/")
def index():
    return render_template("index.html")

# =====================
# 映画一覧 API
# =====================

@app.route("/api/movies")
def api_movies():
    return jsonify(
        movies[["movie_id", "movie_title"]]
        .to_dict(orient="records")
    )

# =====================
# おすすめ API
# =====================

@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    selected_ids = data.get("movie_ids", [])

    # 全体平均
    global_avg = ratings.groupby("movie_id")["rating"].mean()

    # ---------- 未選択 ----------
    if not selected_ids:
        top_ids = global_avg.sort_values(ascending=False).head(5).index
        rec = movies[movies["movie_id"].isin(top_ids)]
        return jsonify(
            rec[["movie_id", "movie_title"]].to_dict(orient="records")
        )

    # ---------- 選択あり ----------
    users = ratings[ratings["movie_id"].isin(selected_ids)]["user_id"].unique()
    candidate = ratings[ratings["user_id"].isin(users)]

    # フォールバック
    if candidate.empty:
        top_ids = global_avg.sort_values(ascending=False).head(5).index
        rec = movies[movies["movie_id"].isin(top_ids)]
        return jsonify(
            rec[["movie_id", "movie_title"]].to_dict(orient="records")
        )

    avg = candidate.groupby("movie_id")["rating"].mean()
    avg = avg.drop(index=selected_ids, errors="ignore")

    if avg.empty:
        top_ids = global_avg.sort_values(ascending=False).head(5).index
        rec = movies[movies["movie_id"].isin(top_ids)]
        return jsonify(
            rec[["movie_id", "movie_title"]].to_dict(orient="records")
        )

    top_ids = avg.sort_values(ascending=False).head(5).index
    rec = movies[movies["movie_id"].isin(top_ids)]

    return jsonify(
        rec[["movie_id", "movie_title"]].to_dict(orient="records")
    )

# =====================
# 起動
# =====================

if __name__ == "__main__":
    app.run(debug=True)
