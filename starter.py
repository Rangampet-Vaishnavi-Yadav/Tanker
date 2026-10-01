"""Improved Tanker Run solver.

Builds routes using nearest-neighbour, then improves them using:
1. 2-opt within each route
2. Moving villages between routes
"""

from adapter import Solver, dist


class StarterSolver(Solver):

    def solve(self, instance, submit_candidate):
        # ---------------------------------------------------------
        # STEP 1: Build initial routes using nearest neighbour
        # ---------------------------------------------------------
        unvisited = set(range(1, instance.size + 1))
        routes = []

        while unvisited:
            route = []
            load = 0
            pos = 0

            while True:
                fits = [
                    v for v in unvisited
                    if load + instance.demand[v] <= instance.capacity
                ]

                if not fits:
                    break

                # Choose nearest village that still fits
                v = min(
                    fits,
                    key=lambda x: (dist(instance, pos, x), x)
                )

                route.append(v)
                load += instance.demand[v]
                pos = v
                unvisited.remove(v)

            routes.append(route)

        # ---------------------------------------------------------
        # STEP 2: Improve each route using 2-opt
        # ---------------------------------------------------------
        for route in routes:
            self.two_opt(instance, route)

        # ---------------------------------------------------------
        # STEP 3: Move villages between routes
        # ---------------------------------------------------------
        improved = True

        while improved:
            improved = False

            # Try every village in every route
            for r1 in range(len(routes)):
                route1 = routes[r1]

                # Work on a copy because the route may change
                for v in list(route1):

                    demand_v = instance.demand[v]

                    # Current distance of route before removing v
                    old_total = self.route_length(instance, route1)

                    # Try putting v into another route
                    for r2 in range(len(routes)):
                        if r1 == r2:
                            continue

                        route2 = routes[r2]

                        # Check capacity
                        if (
                            sum(instance.demand[x] for x in route2)
                            + demand_v
                            > instance.capacity
                        ):
                            continue

                        # Remove v temporarily
                        new_route1 = route1.copy()
                        new_route1.remove(v)

                        # If route becomes empty, that's allowed temporarily
                        # but we don't need to move into another empty route.
                        if not new_route1:
                            new_route1 = []

                        old_route2 = route2.copy()

                        # Try every insertion position
                        best_route2 = None
                        best_cost = float("inf")

                        for pos in range(len(route2) + 1):
                            candidate = route2.copy()
                            candidate.insert(pos, v)

                            cost = self.route_length(
                                instance, candidate
                            )

                            if cost < best_cost:
                                best_cost = cost
                                best_route2 = candidate

                        new_cost = (
                            self.route_length(instance, new_route1)
                            + best_cost
                        )

                        old_cost = (
                            old_total
                            + self.route_length(instance, old_route2)
                        )

                        # Accept only if it improves distance
                        if new_cost + 1e-9 < old_cost:
                            routes[r1] = new_route1
                            routes[r2] = best_route2

                            # Improve both affected routes
                            if routes[r1]:
                                self.two_opt(
                                    instance,
                                    routes[r1]
                                )

                            self.two_opt(
                                instance,
                                routes[r2]
                            )

                            improved = True
                            break

                    if improved:
                        break

                if improved:
                    break

        # ---------------------------------------------------------
        # STEP 4: Remove empty routes
        # ---------------------------------------------------------
        routes = [r for r in routes if r]

        return {"routes": routes}

    # -------------------------------------------------------------
    # Calculate length of one complete route
    # Depot -> villages -> Depot
    # -------------------------------------------------------------
    def route_length(self, instance, route):

        if not route:
            return 0.0

        total = 0.0

        # Depot -> first village
        total += dist(instance, 0, route[0])

        # Village -> village
        for i in range(len(route) - 1):
            total += dist(
                instance,
                route[i],
                route[i + 1]
            )

        # Last village -> depot
        total += dist(instance, route[-1], 0)

        return total

    # -------------------------------------------------------------
    # 2-opt improvement
    # -------------------------------------------------------------
    def two_opt(self, instance, route):

        if len(route) < 3:
            return

        improved = True

        while improved:
            improved = False
            best_gain = 0.0
            best_i = -1
            best_j = -1

            for i in range(len(route) - 1):
                a = 0 if i == 0 else route[i - 1]
                b = route[i]

                for j in range(i + 1, len(route)):
                    c = route[j]
                    d = 0 if j == len(route) - 1 else route[j + 1]

                    old_distance = (
                        dist(instance, a, b)
                        + dist(instance, c, d)
                    )

                    new_distance = (
                        dist(instance, a, c)
                        + dist(instance, b, d)
                    )

                    gain = old_distance - new_distance

                    if gain > best_gain + 1e-9:
                        best_gain = gain
                        best_i = i
                        best_j = j

            if best_gain > 1e-9:
                route[best_i:best_j + 1] = reversed(
                    route[best_i:best_j + 1]
                )
                improved = True
