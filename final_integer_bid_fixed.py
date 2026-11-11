"""정수 패킷 입찰 실험 — 전체 실행 코드.

설치: python -m pip install numpy matplotlib koreanize-matplotlib
실행: python final_integer_bid_fixed.py
설정: python final_integer_bid_fixed.py --trials 100000 --seed 42 --out-dir bid_results
인원 변경: 아래 N 값을 수정한 뒤 프로그램을 처음부터 다시 실행하세요.

원래 규칙:
  1) 대역폭 = round(N(100, 5.17^2)); 총 입찰 후보 = 정수 80..104.
  2) N명의 요청 패킷 수를 균등/무작위로 정수 분배.
  3) 전달량은 비례 배분 후 버림, 손실은 요청량 - 전달량.
  4) 개인별 페널티 = round(총손실 * 1.5 * 개인요청량 / 총입찰량).
  5) 총점 = 총전달량 - 개인별 페널티의 합. 음수 총점도 그대로 유지.

소수 구간의 명시적 정의:
  96+t (0<=t<=1)는 '확률 1-t로 96개, 확률 t로 97개를 입찰'하는
  평균 입찰량이다. 실제 각 회차의 패킷/전달량/손실/페널티는 모두 정수다.
  소수 구간의 평균 점수는 이미 계산한 두 정수 전략의 평균을 가중합한다.
  새로운 난수 오차를 더할 필요가 없으며, 두 끝점보다 높아질 수 없다.
  별도의 '실수 입찰 가중치' 모델을 임의로 도입한 코드는 아니다.

생성 파일: integer_results.csv, fractional_mixture_results.csv,
           integer_scores.png, fractional_mixture.png.
그래프를 생략하려면 --no-plots. 그래프는 창을 띄우지 않고 PNG로 저장한다.
"""
import argparse
import csv
from pathlib import Path

import numpy as np


N = 6  # 인원수. 5명으로 바꾸려면 이 값을 5로 수정하세요.
MU = 100.0
SIGMA = 5.17


def equal_groups(bid, n=None):
    """원래 sim_groups와 같은, 합계가 bid인 정수 균등 분배."""
    if n is None:
        n = N
    base, remainder = divmod(int(bid), n)
    groups = np.full(n, base, dtype=np.int64)
    groups[:remainder] += 1
    return groups


def random_groups(bid, count, rng, n=None):
    """random.sample(range(1,bid), n-1)과 같은 분배 분포.

    서로 다른 정수 절단점을 얻을 때까지 중복이 있는 행만 다시 뽑는다.
    정렬된 절단점 집합은 균등하고, 모든 그룹은 1 이상이다.
    """
    if n is None:
        n = N
    if bid < n:
        raise ValueError("양수 정수 그룹을 만들려면 bid >= n이어야 합니다.")
    if count == 0:
        return np.empty((0, n), dtype=np.int64)
    cuts = np.sort(rng.integers(1, bid, size=(count, n - 1)), axis=1)
    duplicates = np.any(np.diff(cuts, axis=1) == 0, axis=1)
    while duplicates.any():
        cuts[duplicates] = np.sort(
            rng.integers(1, bid, size=(int(duplicates.sum()), n - 1)), axis=1
        )
        duplicates = np.any(np.diff(cuts, axis=1) == 0, axis=1)
    boundaries = np.column_stack((
        np.zeros(count, dtype=np.int64), cuts,
        np.full(count, bid, dtype=np.int64),
    ))
    return np.diff(boundaries, axis=1)


def round_half_even_ratio(numerator, denominator):
    """음이 아닌 유리수를 Python round와 같은 짝수 쪽 반올림으로 정수화.

    예: 1.5 -> 2, 2.5 -> 2. 페널티 계산에서 부동소수점 오차도 피한다.
    """
    quotient, remainder = np.divmod(numerator, denominator)
    up = (2 * remainder > denominator) | (
        (2 * remainder == denominator) & (quotient % 2 == 1)
    )
    return quotient + up.astype(np.int64)


def integer_scores(bid, bandwidths, groups):
    """여러 회차의 정수 점수. groups는 (N,) 또는 (회차수,N)."""
    b = np.asarray(bandwidths)
    g = np.asarray(groups)
    if not isinstance(bid, (int, np.integer)) or bid < N:
        raise ValueError(f"총 입찰량은 인원수 {N} 이상의 정수여야 합니다.")
    if b.ndim != 1 or not np.issubdtype(b.dtype, np.integer):
        raise ValueError("대역폭 배열은 1차원 정수 배열이어야 합니다.")
    if np.any(b < 0):
        raise ValueError("음수 대역폭은 허용하지 않습니다.")
    if not np.issubdtype(g.dtype, np.integer):
        raise ValueError("그룹별 패킷 수는 정수여야 합니다.")
    if g.shape not in ((N,), (len(b), N)):
        raise ValueError(f"groups의 모양은 ({N},) 또는 (회차수, {N})여야 합니다.")
    if np.any(g < 1) or np.any(g.sum(axis=-1) != bid):
        raise ValueError("그룹은 양수이고 그룹 합계는 총 입찰량과 같아야 합니다.")

    # 모든 입력이 음이 아닌 정수이므로 //는 원래 int(g * B / bid)와 같다.
    delivered = np.minimum(g, (g * b[:, None]) // bid)
    delivered_total = delivered.sum(axis=1)
    loss = bid - delivered_total

    # 원래 round(loss * 1.5 * g / bid)와 같은 반올림을 정수 연산으로 수행.
    penalties = round_half_even_ratio(3 * loss[:, None] * g, 2 * bid)
    scores = delivered_total - penalties.sum(axis=1)
    assert np.issubdtype(scores.dtype, np.integer)
    return scores


def choose_integer_bid(average_bid, rng):
    """소수 평균 입찰을 실제 정수 입찰로 구현할 때 사용할 수 있는 함수.

    대역폭을 보기 전에 호출해야 고정 확률 혼합 전략이 된다.
    평균 점수를 구할 때는 이 함수를 재실행하지 않고 가중합을 써도 같다.
    """
    low = int(np.floor(average_bid))
    return low + int(rng.random() < average_bid - low)


def self_test():
    """현재 N에 맞는 분배를 만들고 원래 Python 점수식과 비교한다."""
    def original_score(groups, bandwidth):
        groups = [int(v) for v in groups]
        bid = sum(groups)
        if bid <= bandwidth:
            return bid
        delivered = sum(int(v * bandwidth / bid) for v in groups)
        loss = bid - delivered
        penalties = sum(round(loss * 1.5 * v / bid) for v in groups)
        return delivered - penalties

    rng = np.random.default_rng(1234)

    # 5명일 때만 유효한 [20] * 5, 점수 85 예시를 N명에 일반화한다.
    example_bid = max(100, N)
    example_bandwidth = example_bid - 1
    example_groups = equal_groups(example_bid)
    actual = integer_scores(example_bid, np.array([example_bandwidth]), example_groups)[0]
    assert actual == original_score(example_groups, example_bandwidth)
    if N == 5:
        assert actual == 85  # 원래 5명 예시의 회귀 검증

    # 균등 분배와 무작위 분배 모두, 여러 입찰량/대역폭에서 검증한다.
    for bid in range(max(80, N), max(104, N) + 1):
        b = rng.integers(65, max(121, N + 10), size=100)
        equal = np.tile(equal_groups(bid), (len(b), 1))
        random = random_groups(bid, len(b), rng)
        for g in (equal, random):
            expected = [original_score(groups, int(bandwidth))
                        for groups, bandwidth in zip(g, b)]
            np.testing.assert_array_equal(integer_scores(bid, b, g), expected)


def simulate(trials, seed, start, end, focus_low):
    bandwidth_seed, group_seed = np.random.SeedSequence(seed).spawn(2)
    bandwidth_rng = np.random.default_rng(bandwidth_seed)
    group_rng = np.random.default_rng(group_seed)
    # 원래 round(gauss(...))와 같은 반올림·분포. 모든 후보에 같은 표본 사용.
    bandwidths = np.rint(bandwidth_rng.normal(MU, SIGMA, trials)).astype(np.int64)
    if np.any(bandwidths < 0):
        raise ValueError("음수 대역폭이 발생했습니다. 입력 분포를 확인하세요.")
    results = []
    focus_samples = {"equal": {}, "random": {}}
    for bid in range(start, end + 1):
        congested = bandwidths < bid
        b = bandwidths[congested]
        for mode in ("equal", "random"):
            scores = np.full(trials, bid, dtype=np.int64)
            if len(b):
                groups = (equal_groups(bid) if mode == "equal" else
                          random_groups(bid, len(b), group_rng))
                scores[congested] = integer_scores(bid, b, groups)
            results.append({
                "bid": bid, "mode": mode,
                "mean_score": float(scores.mean()),
                "standard_error": float(scores.std(ddof=1) / np.sqrt(trials)),
            })
            if bid in (focus_low, focus_low + 1):
                focus_samples[mode][bid] = scores
    return results, focus_samples


def make_mixture(results, focus_low):
    lookup = {(r["bid"], r["mode"]): r["mean_score"] for r in results}
    rows = []
    for x in np.linspace(focus_low, focus_low + 1, 101):
        p_high = float(x - focus_low)
        rows.append({
            "average_bid": float(x),
            "low_bid": focus_low,
            "high_bid": focus_low + 1,
            "probability_high_bid": p_high,
            "equal_mean_score": ((1 - p_high) * lookup[(focus_low, "equal")]
                                 + p_high * lookup[(focus_low + 1, "equal")]),
            "random_mean_score": ((1 - p_high) * lookup[(focus_low, "random")]
                                  + p_high * lookup[(focus_low + 1, "random")]),
        })
    for mode in ("equal", "random"):
        values = np.array([r[f"{mode}_mean_score"] for r in rows])
        endpoint_max = max(lookup[(focus_low, mode)], lookup[(focus_low + 1, mode)])
        assert np.all(values <= endpoint_max + 1e-12)
    return rows


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save_plots(results, mixture, out_dir, trials):
    import matplotlib
    matplotlib.use("Agg")
    import koreanize_matplotlib  # noqa: F401 - 한글 글꼴 설정
    import matplotlib.pyplot as plt

    colors = {"equal": "#1751D0", "random": "#E2661E"}
    labels = {"equal": "균등 분배", "random": "무작위 분배"}
    surface, ink, secondary = "#FDFDFF", "#1E2433", "#505A74"

    def style(ax):
        ax.set_facecolor(surface)
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#E2E6F0", linewidth=0.8)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color("#CDD3E0")
        ax.tick_params(colors=secondary)
        ax.xaxis.label.set_color(secondary)
        ax.yaxis.label.set_color(secondary)
        ax.set_ylabel("1회당 평균 점수")

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=surface)
    for mode in ("equal", "random"):
        rows = [r for r in results if r["mode"] == mode]
        ax.errorbar([r["bid"] for r in rows], [r["mean_score"] for r in rows],
                    yerr=[1.96 * r["standard_error"] for r in rows],
                    color=colors[mode], marker="o", markersize=4,
                    linewidth=1.5, capsize=2, label=labels[mode])
        best = max(rows, key=lambda r: r["mean_score"])
        ax.scatter(best["bid"], best["mean_score"], s=75,
                   facecolors=surface, edgecolors=colors[mode], zorder=5)
    style(ax)
    ax.set_xlabel("총 입찰량: 정수 패킷 수")
    ax.set_title(f"정수 입찰량별 평균 점수 · {N}명 · {trials:,}회", color=ink, loc="left")
    ax.set_xticks(list(range(results[0]["bid"], results[-1]["bid"] + 1, 2)))
    ax.legend(frameon=False, labelcolor=secondary)
    fig.text(0.12, 0.025, "각 점은 정수 후보 · 연결선은 시각적 가이드 · 오차막대는 점별 근사 95% 신뢰구간",
             fontsize=9, color="#737D96")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(out_dir / "integer_scores.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    low, high = mixture[0]["low_bid"], mixture[0]["high_bid"]
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=surface)
    for mode in ("equal", "random"):
        ax.plot([r["average_bid"] for r in mixture],
                [r[f"{mode}_mean_score"] for r in mixture],
                color=colors[mode], linewidth=2, label=labels[mode])
    style(ax)
    ax.set_xlim(low, high)
    ax.set_xlabel(f"평균 입찰량: 매회 실제 입찰은 {low}개 또는 {high}개")
    ax.set_title(f"{low}~{high} 구간: 두 정수 전략의 확률 혼합 · {N}명", color=ink, loc="left")
    ax.legend(frameon=False, labelcolor=secondary)
    fig.text(0.12, 0.025, "소수 패킷 전송이 아님 · 혼합 평균은 두 끝점의 가중평균이므로 끝점 최대값을 넘지 않음",
             fontsize=9, color="#737D96")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(out_dir / "fractional_mixture.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="정수 패킷 입찰 시뮬레이션 전체 코드")
    parser.add_argument("--trials", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--start", type=int, default=80)
    parser.add_argument("--end", type=int, default=104)
    parser.add_argument("--focus-low", type=int, default=96)
    parser.add_argument("--out-dir", type=Path, default=Path("bid_results"))
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    if not isinstance(N, int) or isinstance(N, bool) or N < 1:
        parser.error("N은 1 이상의 정수여야 합니다.")
    if args.trials < 2 or args.start < N or args.end < args.start:
        parser.error(f"trials >= 2, start >= N({N}), end >= start여야 합니다.")
    if not (args.start <= args.focus_low < args.end):
        parser.error("focus-low와 focus-low+1이 입찰 범위 안에 있어야 합니다.")

    self_test()
    results, focus_samples = simulate(args.trials, args.seed, args.start,
                                      args.end, args.focus_low)
    mixture = make_mixture(results, args.focus_low)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "integer_results.csv", results)
    write_csv(args.out_dir / "fractional_mixture_results.csv", mixture)

    print(f"원래 점수식과의 일치 검증 통과 | 인원={N} | 횟수={args.trials:,} | seed={args.seed}")
    print("전달량·손실·개인별 페널티·회차별 총점은 정수입니다. 평균 점수는 실수입니다.")
    for mode, label in (("equal", "균등 분배"), ("random", "무작위 분배")):
        best = max((r for r in results if r["mode"] == mode), key=lambda r: r["mean_score"])
        print(f"{label}: 최고 표본평균의 입찰량={best['bid']}, "
              f"평균 점수={best['mean_score']:.6f}, 표준오차={best['standard_error']:.6f}")
        low = args.focus_low
        # 같은 대역폭으로 얻은 두 정수 전략을 회차별로 짝지어 비교한다.
        differences = focus_samples[mode][low] - focus_samples[mode][low + 1]
        diff_mean = float(differences.mean())
        diff_se = float(differences.std(ddof=1) / np.sqrt(args.trials))
        print(f"  {low} - {low+1} 점수 차이: {diff_mean:.6f}, "
              f"근사 95% CI=[{diff_mean-1.96*diff_se:.6f}, {diff_mean+1.96*diff_se:.6f}]")
    print("소수 구간은 정수 전략의 확률 혼합이며, 끝점보다 높은 평균 점수를 만들지 않습니다.")
    if not args.no_plots:
        save_plots(results, mixture, args.out_dir, args.trials)
    print(f"결과 저장 위치: {args.out_dir.resolve()}")


if __name__ == "__main__":
    main()
