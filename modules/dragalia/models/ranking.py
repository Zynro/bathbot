class Ranking:
    def __init__(self):
        return

    @classmethod
    def build_ranking(cls, dps_db):
        """
        Given a dps dict, builds a rankings of overall and each adventurers
        specific element.
        """

        for parse, coab_dict in dps_db.items():
            for coab_dict
            sorted_list = sorted(
                [
                    (
                        dps_db[adven]["internal_name"],
                        int(dps_db[adven]["parse"][parse]["damage"]["dps"]),
                    )
                    for adven in dps_db.keys()
                ],
                key=lambda x: x[1],
                reverse=True,
            )
            rankings_db[parse]["all"] = [i[0] for i in sorted_list]
            for element in CONST.dragalia_elements:
                sorted_list = sorted(
                    [
                        (
                            dps_db[adven]["internal_name"],
                            int(dps_db[adven]["parse"][parse]["damage"]["dps"]),
                        )
                        for adven in dps_db.keys()
                        if dps_db[adven]["element"] == element
                    ],
                    key=lambda x: x[1],
                    reverse=True,
                )
                rankings_db[parse][element] = [i[0] for i in sorted_list]
        return rankings_db
