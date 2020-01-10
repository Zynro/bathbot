class FFLogs:
    def __init__(self, token):
        self.API = "https://www.fflogs.com:443/v1"
        self.token = token

    def generate_fflogs_link(self, character, world, metric="rdps", method="rankings"):
        return f"{self.API}/{method}/character/{character}/{world}/NA?metric={metric}&api_key={self.token}"
