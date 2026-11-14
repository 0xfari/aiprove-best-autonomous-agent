#!/usr/bin/awk -f
BEGIN {
  split("0 9592 17984 25997 33860 41538 49098 56543 63951 71274 78498 85714 92938 100021 107126 114155 121127 128141 135072 142029 148933 155805 162662 169511 176302 183072 189880 196645 203362 210109 216816 223492 230209 236900 243539 250150 256726 263397 269987 276611 283146 289774 296314 302824 309335 315948 322441 328964 335439 341992 348513", T, " ")
}
{
  n = $1 + 0
  if (n < 2) { print 0; exit }
  k = int(n / 100000); base = k * 100000
  cnt = T[k + 1] + (k == 0 ? 1 : 0)
  lim = int(sqrt(n))
  # small primes up to lim
  np = 0
  for (i = 2; i <= lim; i++) {
    if (!isp[i]) {
      ps[++np] = i
      if (i * i <= lim) for (j = i * i; j <= lim; j += i) isp[j] = 1
    }
  }
  lo = base + 1; if (lo < 3) lo = 3
  hi = n
  m = (hi >= lo) ? int((hi - lo) / 2) + 1 : 0
  for (i = 1; i <= m; i++) seg[i] = 1
  for (pi = 1; pi <= np; pi++) {
    p = ps[pi]
    if (p == 2) continue
    start = p * p
    t = int((base + 1 + p - 1) / p) * p
    if (t > start) start = t
    if (start % 2 == 0) start += p
    for (j = start; j <= hi; j += 2 * p) seg[int((j - lo) / 2) + 1] = 0
  }
  for (i = 1; i <= m; i++) if (seg[i]) cnt++
  print cnt
}
