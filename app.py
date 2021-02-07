from flask import Flask, request, jsonify
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)


def process_input(input: dict = None) -> tuple:
    """
    Getting data for powerplants from input. Processing costs and efficiencies
    for formulating minimal flow problem. Here we reformulate the initial problem in the form:

    ∑ c_i•p'_i --> min
    ∑ p'_i = load
    0 ≤ p'_i ≤ p'i_max

    Where p_i are given powers, e_i are efficiencies and p'_i = (p_i - p_i_min) * e_i

    :param input: data loaded from posted payload
    :return: processed powers, costs, load with names of powerplants
    """
    load = input["load"]
    co2_cost = input["fuels"]["co2(euro/ton)"]
    gas_cost = input["fuels"]["gas(euro/MWh)"]
    wind = input["fuels"]["wind(%)"] / 100.0
    kerosine_cost = input["fuels"]["kerosine(euro/MWh)"]
    powerplants = input["powerplants"]

    # Reducing powers on p_min to proceed with restrictions in form 0 ≤ p' ≤ p'_max; p' = p - p_min

    powers = [
        p["efficiency"] * (p["pmax"] - p["pmin"])
        if p["type"] in ["gasfired", "turbojet"]
        else wind * (p["pmax"] - p["pmin"])
        for p in powerplants
    ]

    # Reducing initial load according to the new restrictions

    load -= sum(
        [
            p["efficiency"] * p["pmin"]
            if p["type"] in ["gasfired", "turbojet"]
            else wind * p["pmin"]
            for p in powerplants
        ]
    )
    names = [p["name"] for p in powerplants]

    # Defining costs of the fuels of each powerplant

    costs = []
    for i, powerplant in enumerate(powerplants):
        if powerplant["type"] == "gasfired":
            # For gasfired powerplants costs depend on gas and CO_2 costs
            costs.append(gas_cost / powerplant["efficiency"] + 0.3 * co2_cost)
        elif powerplant["type"] == "turbojet":
            # For turbojets costs depend on kerosin costs
            costs.append(kerosine_cost / powerplant["efficiency"])
        else:
            # For wind turbines costs are 0
            costs.append(0)
    return powers, costs, load, names


def merit_order_optimizer(costs, powers, load, names):
    """
    Solving the optimization problem. Having problem in the form

    ∑ c_i•p_i --> min
    ∑ p_i = load
    0 ≤ p_i ≤ p_i_max

    We first add the cheapest ones then proceed with others in
    ascending order of costs until the desired load is archived.

    :param costs: costs for objective function (c_i)
    :param powers: powers of powerplants (p_i)
    :param load: target value of load
    :param names: names of powerplants
    :return: None if load is infeasible, else list of optimal powers with names
    """
    costs_powers = sorted(list(zip(costs, powers, names)), key=lambda x: x[0])
    optimal_powers = []
    temp_load = 0
    for cost, power, name in costs_powers:
        if temp_load + power < load:
            optimal_powers.append((power, name))
            temp_load += power
        elif temp_load < load:
            optimal_power = load - temp_load
            optimal_powers.append((optimal_power, name))
            temp_load = load
        else:
            optimal_powers.append((0, name))
    if temp_load < load:
        return
    return optimal_powers


class PowerplantSolver(Resource):
    def get(self):
        return

    def post(self):
        input_data = request.get_json(force=True)
        powerplants = input_data["powerplants"]
        powers, costs, load, names = process_input(input_data)
        optimal_powers = merit_order_optimizer(costs, powers, load, names)

        # Proceed result to the desired form of output

        output = []
        if optimal_powers:
            for p, name in optimal_powers:
                powerplant = next(
                    powerpl for powerpl in powerplants if powerpl["name"] == name
                )
                p_min = powerplant["pmin"]
                if powerplant["type"] in ["gasfired", "turbojet"]:
                    efficiency = powerplant["efficiency"]
                else:
                    efficiency = input_data["fuels"]["wind(%)"] / 100.0

                # Go back to p_i = p'_i * e_i + p'i_min

                try:
                    p /= efficiency
                except ZeroDivisionError:
                    pass
                p += p_min
                output.append({"name": name, "p": round(p, 1)})
        else:
            output.append(
                {
                    "message": "The desired load cannot be archived with given set of powerplants"
                }
            )
        return jsonify(output)


api.add_resource(PowerplantSolver, "/productionplan")

if __name__ == "__main__":
    app.run(debug=True, port=8888)
