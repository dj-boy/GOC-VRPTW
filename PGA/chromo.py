import random
from tools import GlobalMap
from PGA.route import Route

center_id = 0
custom_number = 1000
station_number = 100
random_add_station = 2

max_volume = 16
max_weight = 2.5
unload_time = 0.5
driving_range = 120000
charge_tm = 0.5
charge_cost = 50
wait_cost = 24
depot_wait = 1
depot_open_time = 16.  # suppose first vehicle start at 8:00
unit_trans_cost = 14. / 1000
vehicle_cost = 300


class Chromo:
    g_map: GlobalMap
    sequence: list

    def __init__(self, sequence=None, g_map=None, idx=0, punish=9999, reset_window=True):
        self.idx = idx
        self.g_map = g_map
        self.sequence = sequence
        self.punish = punish
        self.reset_window = reset_window
        self.cost = 0
        self.vehicle_number = 0
        self.rank = 0
        if self.sequence is None:
            self.__random_init__()
        self.refresh_state()

    def refresh_state(self):
        """
        refresh state of this chromo
        :return: None
        """
        self.cost = 0
        self.vehicle_number = len(self.sequence)
        start_list = [depot_open_time]
        for route in self.sequence:
            assert isinstance(route, Route)
            self.cost += route.cost  # pure route cost
            self.cost += vehicle_cost  # new vehicle cost
            start_list.append(route.start_time)  # record each route start time
        # reuse some vehicles
        start_list.sort()
        pos_1 = 0
        pos_2 = 0
        while pos_2 < len(start_list):
            if start_list[pos_2] - start_list[pos_1] >= depot_wait:  # an old vehicle is again usable
                self.cost += depot_wait * wait_cost - vehicle_cost  # replace new-vehicle cost as wait cost
                pos_1 += 1
                self.vehicle_number -= 1
            pos_2 += 1

    def get_fitness(self):
        return 1 / self.cost

    def get_score(self):
        return self.cost - self.vehicle_number * vehicle_cost, self.vehicle_number

    def reset_rank(self):
        self.rank = 0

    def __random_init__(self):
        """
        random init this chromo by some prior experience (when no data is given)
        :return: None
        """
        # random add charging station and shuffle all customer and station
        temp_station = random_add_station * list(range(custom_number + 1, custom_number + station_number + 1))
        random.shuffle(temp_station)
        temp_station = temp_station[:int((random.random() / 2 + 0.1) * random_add_station)]
        temp_node = list(range(1, custom_number + 1)) + temp_station
        random.shuffle(temp_node)

        # init all route, i.e. self.sequence
        capacity = driving_range
        weight, volume = max_weight, max_volume
        temp_route = []
        pre_node = center_id
        for node in temp_node:
            capacity -= self.g_map.get_distance(pre_node, node)
            if node <= custom_number:
                demand = self.g_map.get_demand(node)
                weight -= demand[0]
                volume -= demand[1]
            else:
                capacity = driving_range
            if capacity < 0 or weight < 0 or volume < 0:
                time_weight = random.random()
                temp_route.sort(key=lambda x: time_weight * self.g_map.get_window(x)[0]
                                + (1 - time_weight) * self.g_map.get_window(x)[1])
                self.sequence.append(Route(sequence=temp_route, g_map=self.g_map, punish=self.punish))
                capacity = driving_range
                weight, volume = max_weight, max_volume
                temp_route = []
                pre_node = center_id
