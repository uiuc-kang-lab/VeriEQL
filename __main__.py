# -*- coding: utf-8 -*-

from constants import DIALECT
from environment import Environment


def main(sql1, sql2, schema, ROW_NUM=2, constraints=None, **kwargs):
    with Environment(**kwargs) as env:
        for k, v in schema.items():
            env.create_database(attributes=v, bound_size=ROW_NUM, name=k)
        env.add_constraints(constraints)
        env.save_checkpoints()
        if env._script_writer is not None:
            env._script_writer.save_checkpoints()
        result = env.analyze(sql1, sql2, out_file="test/test.py")
        if env.show_counterexample:
            print(env.counterexample)
        if env.traversing_time is not None:
            print(f"Time cost: {env.traversing_time + env.solving_time:.2f}")
        if result == True:
            print("\033[1;32;40m>>> Equivalent! \033[0m")
        else:
            print("\033[1;31;40m>>> Non-Equivalent! Found a counterexample! \033[0m")


if __name__ == '__main__':
    sql1, sql2 = [
        "SELECT DISTINCT PAGE_ID AS RECOMMENDED_PAGE FROM (SELECT CASE WHEN USER1_ID=1 THEN USER2_ID WHEN USER2_ID=1 THEN USER1_ID ELSE NULL END AS USER_ID FROM FRIENDSHIP) AS TB1 JOIN LIKES AS TB2 ON TB1.USER_ID=TB2.USER_ID WHERE PAGE_ID NOT IN (SELECT PAGE_ID FROM LIKES WHERE USER_ID=1)",
        "SELECT DISTINCT PAGE_ID AS RECOMMENDED_PAGE FROM (SELECT B.USER_ID, B.PAGE_ID FROM FRIENDSHIP A LEFT OUTER JOIN LIKES B ON (A.USER2_ID=B.USER_ID OR A.USER1_ID=B.USER_ID) AND (A.USER1_ID=1 OR A.USER2_ID=1) WHERE B.PAGE_ID NOT IN (SELECT DISTINCT PAGE_ID FROM LIKES WHERE USER_ID=1)) T",
    ]
    # FRIENDSHIP: (USER1_ID, USER2_ID) [PK]
    # LIKES: (USER_ID, PAGE_ID) [PK]
    schema = {"FRIENDSHIP": {"USER1_ID": "INT", "USER2_ID": "INT"}, "LIKES": {"USER_ID": "INT", "PAGE_ID": "INT"}, }
    constants = [
        # use `__` to replace `.`, e.g., FRIENDSHIP.USER1_ID => FRIENDSHIP__USER1_ID
        {"primary": [{"value": "FRIENDSHIP__USER1_ID"}, {"value": "FRIENDSHIP__USER2_ID"}]},
        {"primary": [{"value": "LIKES__USER_ID"}, {"value": "LIKES__PAGE_ID"}]},
        {"neq": [{"value": "FRIENDSHIP__USER1_ID"}, {"value": "FRIENDSHIP__USER2_ID"}]},
    ]
    bound_size = 2
    # generate_code: generate SQL code and running outputs if you find a counterexample
    # timer: show time costs
    # show_counterexample: print counterexample?
    config = {'generate_code': True, 'timer': True, 'show_counterexample': True, "dialect": DIALECT.MYSQL}
    main(sql1, sql2, schema, ROW_NUM=bound_size, constraints=constants, **config)
