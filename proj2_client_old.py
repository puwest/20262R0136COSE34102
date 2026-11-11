#!/usr/bin/env python3
"""Proj2 student skeleton: one program, one student account.

    python -m pip install requests
    python proj2_client.py --student-id YOUR_STUDENT_ID
    python proj2_client.py --student-id YOUR_STUDENT_ID --week 2

Week 1 is the default. Week 2 opens on 23 October 2026, 00:00 KST.
To test both networks, run the same file in two terminals, one per week.

Edit only the Algorithm class. Each teammate runs their own copy on their own
computer, and teammates may use different algorithms. All teammates must keep
running their programs until the 1,000-round attempt finishes.

For each round, the client calls choose_bid(observation), submits your bid,
waits for all teammates, then calls on_result(result) with your feedback.
The same Algorithm object is reused: store values on self to remember them
between rounds. Login, requests, waiting and retries are handled for you.
"""
import argparse
import time
import random

import requests


# ---------- Your work: edit the methods in this class ----------
class Algorithm:
    def __init__(self):
        # self.offset = (abs(hash(id(self)) + id(object())) % 10)-4.5 * 0.09
        self.initial = 0
        self.prop = 0.0                 #아마 안쓸듯?
        self.window = 0.0
        self.bound = 0                  #현재 클라이언트가 보낼 수 있는 최대 bound. 갑자기 확 깎이면 week2로 간주, 조금 늘어나면 다른 클라이언트가 일을 다해서 좀 여유가 생겼다고 생각할 수 있음.
        self.bound_decision_row = 6     #얼마나 loss 0이 유지되었을 때 bound를 늘릴 것인가
        self.decrease = 0.6
        self.last_bid_queue = [0 for i in range(10)]        #append로 마지막에 삽입 + pop(0)으로 가장 오래된거 pop. [older...newer] 일단 10줄로 생각.
        self.last_delivery_queue = [0 for i in range(10)]   #append로 마지막에 삽입 + pop(0)으로 가장 오래된거 pop. [older...newer] 일단 10줄로 생각.
        self.last_loss_queue = [0 for i in range(10)]       #append로 마지막에 삽입 + pop(0)으로 가장 오래된거 pop. [older...newer] 일단 10줄로 생각.
        self.last_panelty_queue = [0 for i in range(10)]       #append로 마지막에 삽입 + pop(0)으로 가장 오래된거 pop. [older...newer] 일단 10줄로 생각.
        self.total_bid = 0
        self.total_delivered = 0
        self.total_loss = 0
        self.total_panelty = 0
        # Called once when this program prepares or joins an attempt.
        # Initialize values you want to remember between rounds on self
        # (for example, self.last_loss = 0). Local variables do not persist.
        pass

    def choose_bid(self, observation: dict) -> int:
        """Choose your next bid using your own state and previous feedback.

        observation is a dictionary supplied by the client, with your own
        data in the nested dictionary observation["player"]. Useful fields:

        observation["round"]:
            Round you are bidding for (1 through 1,000).
        observation["player"]["remaining"]:
            Data you still need to deliver before this round. Penalties can
            increase it; it is not necessarily smaller than last round.
        observation["player"]["delivered"]:
            Total data you have successfully delivered in completed rounds
            of this attempt (0 at the start), not just the previous round.

        Return a Python int from 0 to remaining, inclusive. A bid is the
        amount you TRY to send; actual delivery may be smaller. Return 0
        to send nothing this round. Do not return a float, string or None.
        Example: with remaining == 3, the valid bids are 0, 1, 2 and 3.

        Earlier completed rounds are passed to on_result() before this call.
        Use state saved on self there to make your next decision. There is
        no previous feedback at the start of a new attempt.
        """
        #week1 일 때
        """ 
        """
        if observation["me"]["id"] == "2025320057P1":
            return 16
        if observation["me"]["id"] == "2025320057P2":
            return 18
        if observation["me"]["id"] == "2025320057P3":
            return 20
        if observation["me"]["id"] == "2025320057P4":
            return 22
        if observation["me"]["id"] == "2025320057P5":
            return 
        # 라운드 1에 각자가 보내야할 총 량을 저장할 필요가 없음.
        # if observation["round"] == 1:
        #     self.initial = observation["player"]["remaining"]
        #     self.bound = round((self.initial / 100000) * 100)
        #     self.window = float(self.bound)
        #     return min(self.bound, observation["player"]["remaining"])

        # if self.last_loss_queue[-1] > 0 or self.last_panelty_queue[-1] > 0:
        #     # 1. 혼잡 피해 심각도 계산 (입찰량 대비 손실+패널티 비율)
        #     severity = min(1.0, (self.last_loss_queue[-1] + self.last_panelty_queue[-1]) / self.last_bid_queue[-1])
        #     # 2. 심각도에 비례하여 최대 허용 입찰 속도(window) 감소
        #     self.window = max(1.0, self.window * (1.0 - self.decrease * severity))
        # else:
        #     self.window += getattr(self, 'increase', 0.2)
        # candidate_bid = self.last_bid_queue[-1]
        # if self.last_bid_queue[-1] < self.bound - 5:      #slow start
        #     candidate_bid = self.last_bid_queue[-1] + 3
        # if self.last_loss_queue[-1] > 0:    #바로 이전에 loss가 있었다면?(하지만 week1의 loss는 그냥 운이 안좋아서 생긴거임.)
        #     if sum(self.last_loss_queue) > round(((self.initial / 100000) * 100)/2.7):   #이거 bound가 너무 높아졌다....
        #         self.bound -= 1
        #     return min(self.last_bid_queue[-1] - 1, observation["player"]["remaining"])
        # if self.last_loss_queue[-self.bound_decision_row:] == [0] * self.bound_decision_row and observation["round"] > 10: #내가 판단하기에 얘는 조금 커졌다.
        #     self.bound += 1
        #     candidate_bid = self.last_bid_queue[-1] + 1
        # if self.bound > self.last_bid_queue[-1] + 1:
        #     candidate_bid = self.last_bid_queue[-1] + 1


        # final_bid = min(candidate_bid, int(self.window))
        # if candidate_bid < int(self.window):
        #     print("기존거")
        # elif candidate_bid > int(self.window):
        #     print("요즘꺼")
        # return min(final_bid, observation["player"]["remaining"])

        
        # return min(500, observation["player"]["remaining"])
        # Starter behavior: send 5 each round (or the smaller remaining amount).
        

    def on_result(self, result: dict) -> None:
        """Update your controller after each completed round.

        result is a dictionary describing ONE completed round:
            result["round"]:     round that just completed
            result["bid"]:       amount you requested in that round
            result["delivered"]: amount actually delivered in that round
            result["lost"]:      undelivered part of your bid (bid - delivered)
            result["penalty"]:   extra data added to your remaining workload
            result["before"]:    your remaining data before that round
            result["after"]:     your remaining data after that round

        after = before - delivered + penalty
        Lost data is already in remaining; do not add lost again.
        For example, before=100, bid=5, delivered=3, lost=2, penalty=3
        gives after=100. The delivered value here is for this round only;
        observation["player"]["delivered"] is the cumulative total.`

        Save any feedback you need on self; this method returns nothing.
        Current bandwidth and other students' workloads or bids are not provided.
        """
        self.last_bid_queue.pop(0)
        self.last_bid_queue.append(result["bid"])
        self.last_delivery_queue.pop(0)
        self.last_delivery_queue.append(result["delivered"])
        self.last_loss_queue.pop(0)
        self.last_loss_queue.append(result["lost"])
        self.last_panelty_queue.pop(0)
        self.last_panelty_queue.append(result["penalty"])
        self.total_bid += result["bid"]
        self.total_delivered += result["delivered"]
        self.total_loss += result["lost"]
        self.total_panelty += result["penalty"]
        print(f"{result["round"]} round / bound: {self.bound} / {self.last_bid_queue[-1]} bid / {self.last_delivery_queue[-1]} delivered / {self.last_loss_queue[-1]} loss / {self.last_panelty_queue[-1]} panelty")
        if round(self.last_loss_queue[-1] * 1.5) >  self.last_panelty_queue[-1]:       #round(4.5) == 4?????
            print("[!] panelty 이득")
        if round(self.last_loss_queue[-1] * 1.5) <  self.last_panelty_queue[-1]: 
            print("[!] panelty 손해")
        if result["round"] % 100 == 0:
            print(f"중간점검: {self.total_bid} 할당됨 {self.total_delivered} 전달됨 / {self.total_loss} 손실 / {self.total_panelty} 패널티")

        # Use this feedback to update your controller's state.
        # print(result["round"],"단계 high", self.high_stack,"low:",self.low_stack,"이고 총 bid / loss:",self.total_bid,"/",self.total_loss, "high->low loss:",self.shrink_loss)
        # if result["round"] == 1000:
        #     print("끝. HH:",self.hh,"HL:",self.hl,"LH:",self.lh,"LL:",self.ll,"total_bid:",self.total_bid,"total_panelty:",self.total_loss*1.5,"shrink_panelty:",self.shrink_loss*1.5,"high_panelty:",self.high_loss*1.5,"+low panelty:",self.low_loss_by50*1.5)
        
        pass


# ---------- HTTP client: leave the code below unchanged ----------
# You can implement your controller using only the class above.
# This section logs in, submits one bid per round and retrieves your feedback.
# When remaining reaches 0, it skips choose_bid() and submits 0 automatically;
# keep the program running so your team can complete all 1,000 rounds.
def run(base, student_id, password, poll_seconds=0.1, week=1):
    url = base.rstrip("/")
    if not url.endswith("/proj2"):
        url += "/proj2"
    with requests.Session() as http:
        def request(method, path, **kwargs):
            # Select the week on every request; two programs can use the same ID.
            kwargs["params"] = {**kwargs.get("params", {}), "week": week}
            # If a response is lost, retry the exact same request safely.
            while True:
                try:
                    response = http.request(method, url + path, timeout=(3, 10), **kwargs)
                    if response.status_code >= 500:
                        response.raise_for_status()
                    if not response.ok:
                        raise RuntimeError(response.json().get("error", "Request failed."))
                    return response.json()
                except (requests.Timeout, requests.ConnectionError, requests.HTTPError):
                    print(f"[{student_id}] Connection interrupted; retrying.")
                    time.sleep(1)

        request("POST", "/login", json={"student_id": student_id, "password": password})
        state = request("GET", "/api/me")
        if not state["player"]:
            raise RuntimeError("Your student ID has not been assigned to a team.")
        run_id = request("POST", "/api/ready", json={"run_id": state["run_id"]})["run_id"]
        algorithm, seen_round = Algorithm(), 0
        print(f"[{student_id}] Week {week} connected. Waiting for every teammate's own program.")

        def feedback(result):
            nonlocal seen_round
            # Polling/retries can return the same result; process it only once.
            if result["round"] <= seen_round:
                return
            algorithm.on_result(result)
            seen_round = result["round"]
            print(f"[{student_id}] R{seen_round:04d} bid={result['bid']} delivered={result['delivered']} "
                  f"lost={result['lost']} penalty={result['penalty']} left={result['after']}")

        while True:
            state = request("GET", "/api/me", params={"after_round": seen_round})
            if state["run_id"] != run_id:
                raise RuntimeError("Your team prepared another attempt. Restart your program to join it.")
            for result in state["player"]["history"]:
                # Also recover any missed feedback when joining an active run.
                feedback(result)
            if state["phase"] == "aborted":
                raise RuntimeError(state["abort_reason"] + " Restart all teammates' programs to retry.")
            if state["phase"] == "finished":
                print(f"[{student_id}] Week {week} completed. Team standing:", state.get("standing"))
                return state["grade"]
            player = state["player"]
            amount = player["bid"]  # Resume a request already accepted by the server.
            if amount is None:
                amount = 0 if player["remaining"] == 0 else algorithm.choose_bid(state)
            if type(amount) is not int or not 0 <= amount <= player["remaining"]:
                raise ValueError("choose_bid must return an integer from 0 to your remaining data.")
            receipt = request("POST", "/api/bid", json={"run_id": run_id, "round": state["round"], "bid": amount})
            while receipt["status"] == "waiting":
                # Your bid is accepted; wait until every teammate has submitted.
                time.sleep(poll_seconds)
                receipt = request("GET", "/api/result", params={"run_id": run_id, "round": state["round"]})
            feedback(receipt["result"])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--student-id", required=True, help="Your own student ID.")
    parser.add_argument("--base-url", default="http://www.toysugang.korea.ac.kr")
    parser.add_argument("--week", type=int, choices=[1, 2], default=1, help="Network to use (default: 1).")
    args = parser.parse_args()
    try:
        run(args.base_url, args.student_id, "1111", week=args.week)
    except KeyboardInterrupt:
        print("Client stopped. Missing requests for 60 seconds will stop your team's attempt.")
    except (RuntimeError, ValueError, requests.RequestException) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
