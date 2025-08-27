import instaloader

# 取得したいアカウント ID
acct = ""   # ←ここを任意の公開アカウントIDに変更

# Instaloader インスタンス作成
L = instaloader.Instaloader()

# プロフィール取得
profile = instaloader.Profile.from_username(L.context, acct)

# 投稿数、フォロワー数を取得
post_count = profile.mediacount
follower_count = profile.followers

# 結果表示
print(f"アカウント: {acct}")
print(f"投稿数: {post_count}")
print(f"フォロワー数: {follower_count}")
