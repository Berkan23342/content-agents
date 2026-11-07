import React from 'react';
import {C, FireGlow, H, Moon, Skyline, Stars, W, Walker, flicker, hash, lerp} from './art';
import type {Params} from './scenes';

// More places, so the stories do not keep returning to the same few rooms. Same conventions as scenes.tsx:
// p = the beat's settings, f = frame, s = this part's seed, place = the story's seed.
type SceneProps = {p: Params; f: number; s?: number; place?: number};

const num = (v: unknown, d: number) => (typeof v === 'number' ? v : d);
const str = (v: unknown, d: string) => (typeof v === 'string' ? v : d);

const Svg: React.FC<{children: React.ReactNode}> = ({children}) => (
	<svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: 'absolute', inset: 0}}>
		{children}
	</svg>
);

const lightLevel = (light: string, f: number, seed: number) => (light === 'on' ? 1 : light === 'off' ? 0.08 : flicker(f, seed, 0.7));

/** A one-point corridor (walls, floor, ceiling lights) that the indoor scenes below decorate. */
const Corridor: React.FC<{f: number; light: string; wall: string; wall2: string; floor: string; ceiling: string; seed: number}> = ({f, light, wall, wall2, floor, ceiling, seed}) => {
	const vx0 = 430;
	const vx1 = 650;
	const vy0 = 760;
	const vy1 = 1000;
	return (
		<g>
			<path d={`M0 0 L${W} 0 L${vx1} ${vy0} L${vx0} ${vy0} Z`} fill={ceiling} />
			<path d={`M0 ${H} L${W} ${H} L${vx1} ${vy1} L${vx0} ${vy1} Z`} fill={floor} />
			<path d={`M0 0 L${vx0} ${vy0} L${vx0} ${vy1} L0 ${H} Z`} fill={wall} />
			<path d={`M${W} 0 L${vx1} ${vy0} L${vx1} ${vy1} L${W} ${H} Z`} fill={wall2} />
			<rect x={vx0} y={vy0} width={vx1 - vx0} height={vy1 - vy0} fill="#08090d" />
			{[0.1, 0.32, 0.52, 0.7].map((t, i) => {
				const y = lerp(0, vy0, t) + 8;
				const w = lerp(240, 46, t);
				const o = light === 'flicker' ? flicker(f, seed + i * 5, 0.72) : lightLevel(light, f, seed);
				return (
					<g key={i}>
						<rect x={540 - w / 2} y={y} width={w} height={lerp(24, 6, t)} fill="#f2f6ee" opacity={0.15 + 0.85 * o} />
						<ellipse cx={540} cy={y + 36} rx={w * 1.4} ry={lerp(150, 38, t)} fill="#f4fff2" opacity={0.1 * o} />
					</g>
				);
			})}
		</g>
	);
};

/** Walkers standing at different depths down a corridor. */
const CorridorCrowd: React.FC<{n: number; f: number; s: number}> = ({n, f, s}) => (
	<>
		{Array.from({length: n}, (_, i) => {
			const d = 0.15 + hash(i + s + 31) * 0.6;
			return <Walker key={i} x={540 + (hash(i + s) - 0.5) * lerp(120, 700, d)} y={lerp(1000, 1800, d)} h={lerp(200, 760, d)} frame={f} seed={i + s} flip={hash(i + s + 2) < 0.5} eyes={d > 0.4} />;
		})}
	</>
);

const darkness = (light: string, f: number, seed: number) => <rect width={W} height={H} fill="#02030a" opacity={0.72 - 0.55 * lightLevel(light, f, seed)} />;

// ---------------------------------------------------------------- outdoors
/** The lake at night: the far shore, a dock, the moon on the water. zombies: heads rising out of the water. canoe: tied to the dock. */
export const Lake: React.FC<SceneProps> = ({p, f, s = 0}) => {
	const zombies = num(p.zombies, 0);
	const mx = 260 + hash(s) * 560;
	return (
		<Svg>
			<rect width={W} height={920} fill="url(#nightSky)" />
			<Stars frame={f} n={70} maxY={800} seed={s} />
			<Moon x={mx} y={300} r={60} />
			{Array.from({length: 18}, (_, i) => {
				const x = i * 64 - 20 + hash(i + s) * 30;
				const h = 120 + hash(i + 7 + s) * 140;
				return <path key={i} d={`M${x} ${920 - h} L${x + 40} 920 L${x - 40} 920 Z`} fill="#0d1422" />;
			})}
			<rect y={920} width={W} height={1000} fill="#0a1422" />
			<rect y={920} width={W} height={160} fill="#22355a" opacity={0.45} />
			{Array.from({length: 26}, (_, i) => (
				<rect key={i} x={mx - 40 + Math.sin(f / 9 + i) * 30} y={940 + i * 22} width={80 - i * 2} height={5} fill="#f3ecd2" opacity={0.35 - i * 0.012} />
			))}
			{Array.from({length: zombies}, (_, i) => {
				const x = 140 + hash(i + s + 3) * 800;
				const y = 1040 + hash(i + s + 5) * 300;
				const rise = 0.5 + 0.5 * Math.sin(f / 50 + i * 2);
				return (
					<g key={i}>
						<ellipse cx={x} cy={y + 4} rx={50 + rise * 30} ry={10} fill="none" stroke="#9fb4d0" strokeWidth={2} opacity={0.3} />
						<circle cx={x} cy={y - rise * 26} r={20} fill={C.ink} />
						<path d={`M${x - 26} ${y} Q${x} ${y - 40 * rise} ${x + 26} ${y} Z`} fill={C.ink} />
						<circle cx={x + 6} cy={y - rise * 28} r={2.5} fill="#e8f0d0" opacity={0.8 * rise} />
					</g>
				);
			})}
			<path d="M380 1920 L470 1180 L610 1180 L700 1920 Z" fill="#3a2a1e" />
			{Array.from({length: 12}, (_, i) => {
				const t = i / 12;
				const y = lerp(1180, 1920, t * t);
				return <line key={i} x1={lerp(470, 380, t * t)} y1={y} x2={lerp(610, 700, t * t)} y2={y} stroke="#24180f" strokeWidth={lerp(2, 8, t)} />;
			})}
			{p.canoe ? (
				<g transform={`translate(760 1420) rotate(-12) translate(0 ${Math.sin(f / 20) * 6})`}>
					<path d="M-150 0 Q0 60 150 0 Q0 30 -150 0 Z" fill="#7a3a22" />
					<path d="M-150 0 Q0 20 150 0" stroke="#4a2414" strokeWidth={6} fill="none" />
				</g>
			) : null}
			<rect x={0} y={880} width={W} height={160} fill="#7a88a8" opacity={0.16} filter="url(#blur24)" />
		</Svg>
	);
};

/** A gas station on an empty road at night. light: on, flicker or off. car: one left at a pump. zombies: on the forecourt. */
export const GasStation: React.FC<SceneProps> = ({p, f, s = 0}) => {
	const light = str(p.light, 'flicker');
	const on = lightLevel(light, f, 13);
	const zombies = num(p.zombies, 0);
	return (
		<Svg>
			<rect width={W} height={H} fill="url(#nightSky)" />
			<Stars frame={f} n={50} maxY={600} seed={s + 3} />
			<Skyline base={1150} seed={60 + (s % 40)} color="#0e1424" maxH={200} lit={0.02} />
			<rect y={1150} width={W} height={770} fill="#16181e" />
			<rect x={680} y={760} width={420} height={400} fill="#20242e" />
			{[720, 860, 1000].map((x, i) => (
				<rect key={i} x={x} y={860} width={110} height={150} fill="#f6e7b8" opacity={0.15 + 0.6 * on * flicker(f, i + 40, 0.9)} />
			))}
			<rect x={60} y={640} width={34} height={520} fill="#1d212b" />
			<rect x={10} y={520} width={140} height={140} rx={10} fill="#c0392b" opacity={0.25 + 0.6 * on} />
			<rect x={40} y={700} width={680} height={70} fill="#d8dde6" />
			<rect x={40} y={770} width={680} height={14} fill="#fff8de" opacity={0.2 + 0.8 * on} />
			<path d={`M60 784 L700 784 L860 1500 L-100 1500 Z`} fill="#fff6d2" opacity={0.1 * on} />
			{[220, 520].map((x, i) => (
				<g key={i}>
					<rect x={x - 20} y={784} width={40} height={460} fill="#2a2e38" />
					<rect x={x - 60} y={1000} width={120} height={240} rx={14} fill="#3b404c" />
					<rect x={x - 40} y={1030} width={80} height={60} rx={6} fill="#86b3a0" opacity={0.2 + 0.5 * on} />
				</g>
			))}
			{p.car ? (
				<g transform="translate(330 1420)">
					<path d="M-210 0 L-170 -90 L80 -110 L190 -40 L210 0 Z" fill="#3b4a63" />
					<path d="M-150 -86 L60 -104 L150 -46 L-160 -40 Z" fill="#0d111b" />
					<circle cx={-130} cy={0} r={46} fill="#0a0c12" />
					<circle cx={140} cy={0} r={46} fill="#0a0c12" />
					<circle cx={208} cy={-30} r={12} fill="#ffad33" opacity={Math.floor(f / 14) % 2 ? 0.95 : 0.15} />
				</g>
			) : null}
			{Array.from({length: zombies}, (_, i) => {
				const d = 0.3 + hash(i + s + 8) * 0.7;
				const dir = hash(i + s) < 0.5 ? 1 : -1;
				const x = ((hash(i + s + 4) * 1300 + f * dir * (0.4 + d * 0.6)) % 1300 + 1300) % 1300 - 110;
				return <Walker key={i} x={x} y={lerp(1300, 1880, d)} h={lerp(200, 560, d)} frame={f} seed={i + s} flip={dir < 0} eyes={d > 0.6} />;
			})}
			{darkness(light, f, 13)}
		</Svg>
	);
};

// ---------------------------------------------------------------- indoors
/** A supermarket aisle. light: on, flicker or off. empty: the shelves are almost bare. zombies: down the aisle. */
export const Supermarket: React.FC<SceneProps> = ({p, f, s = 0}) => {
	const light = str(p.light, 'flicker');
	const colors = ['#c0392b', '#e67e22', '#f1c40f', '#27ae60', '#2980b9', '#8e44ad', '#ecf0f1'];
	const fill = p.empty ? 0.15 : 0.85;
	return (
		<Svg>
			<Corridor f={f} light={light} wall="#2a2f38" wall2="#262a33" floor="#2d2f33" ceiling="#1b1e25" seed={21} />
			{[true, false].map((left) =>
				[0, 1, 2, 3, 4].map((row) => {
					const items = [];
					for (let k = 0; k < 9; k++) {
						const t0 = k / 9;
						const t1 = (k + 0.8) / 9;
						const xa = left ? lerp(0, 430, t0) : lerp(W, 650, t0);
						const xb = left ? lerp(0, 430, t1) : lerp(W, 650, t1);
						const top = (t: number) => lerp(lerp(0, 760, t), lerp(H, 1000, t), 0.15 + row * 0.15);
						if (hash(row * 31 + k + s + (left ? 0 : 99)) < fill) {
							items.push(<polygon key={k} points={`${xa},${top(t0)} ${xb},${top(t1)} ${xb},${top(t1) + lerp(80, 14, t1)} ${xa},${top(t0) + lerp(80, 14, t0)}`} fill={colors[Math.floor(hash(k * 7 + row + s) * colors.length)]} opacity={0.75} />);
						}
					}
					return <g key={`${left}-${row}`}>{items}</g>;
				}),
			)}
			<CorridorCrowd n={num(p.zombies, 0)} f={f} s={s} />
			{darkness(light, f, 21)}
		</Svg>
	);
};

/** A hospital corridor: pale green walls, a gurney, doors with round windows. light: on, flicker or off. zombies. */
export const Hospital: React.FC<SceneProps> = ({p, f, s = 0}) => {
	const light = str(p.light, 'flicker');
	return (
		<Svg>
			<Corridor f={f} light={light} wall="#2e4440" wall2="#2a3e3a" floor="#3a4542" ceiling="#22302d" seed={33} />
			<rect x={455} y={790} width={170} height={210} fill="#5a6b66" />
			<line x1={540} y1={790} x2={540} y2={1000} stroke="#2a3330" strokeWidth={4} />
			<circle cx={498} cy={850} r={22} fill="#a9d6c8" opacity={0.35 * lightLevel(light, f, 33)} />
			<circle cx={582} cy={850} r={22} fill="#a9d6c8" opacity={0.35 * lightLevel(light, f, 33)} />
			{[0.2, 0.5].map((t, i) => (
				<line key={i} x1={lerp(0, 430, t)} y1={lerp(1150, 900, t)} x2={lerp(0, 430, t + 0.25)} y2={lerp(1150, 900, t + 0.25)} stroke="#6f8d84" strokeWidth={lerp(14, 4, t)} />
			))}
			<g transform="translate(820 1500)">
				<rect x={-200} y={-60} width={400} height={40} rx={10} fill="#c8d2cf" />
				<rect x={-190} y={-20} width={10} height={180} fill="#55605c" />
				<rect x={180} y={-20} width={10} height={180} fill="#55605c" />
				<path d="M-160 -60 Q-60 -110 60 -70 L140 -60 Z" fill="#e6ece9" opacity={0.85} />
			</g>
			<CorridorCrowd n={num(p.zombies, 0)} f={f} s={s} />
			{darkness(light, f, 33)}
		</Svg>
	);
};

/** A school corridor with lockers on both sides and papers on the floor. light: on, flicker or off. zombies. */
export const School: React.FC<SceneProps> = ({p, f, s = 0, place = 0}) => {
	const light = str(p.light, 'flicker');
	const locker = ['#2f5d8a', '#8a2f2f', '#2f7a4a', '#7a6a2f'][place % 4];
	return (
		<Svg>
			<Corridor f={f} light={light} wall="#3a3530" wall2="#35302b" floor="#4a463e" ceiling="#26231f" seed={44} />
			{[true, false].map((left) =>
				Array.from({length: 14}, (_, k) => {
					const t0 = k / 14;
					const t1 = (k + 0.85) / 14;
					const x = (t: number) => (left ? lerp(0, 430, t) : lerp(W, 650, t));
					const top = (t: number) => lerp(lerp(0, 760, t), lerp(H, 1000, t), 0.22);
					const bot = (t: number) => lerp(lerp(0, 760, t), lerp(H, 1000, t), 0.92);
					return <polygon key={`${left}${k}`} points={`${x(t0)},${top(t0)} ${x(t1)},${top(t1)} ${x(t1)},${bot(t1)} ${x(t0)},${bot(t0)}`} fill={locker} stroke="#1c1f26" strokeWidth={lerp(6, 1, t0)} />;
				}),
			)}
			{Array.from({length: 9}, (_, i) => (
				<rect key={i} x={200 + hash(i + s) * 680} y={1500 + hash(i + s + 3) * 380} width={70} height={90} fill="#e9e4d6" opacity={0.6} transform={`rotate(${hash(i + s + 6) * 80 - 40} ${240 + hash(i + s) * 680} ${1540 + hash(i + s + 3) * 380})`} />
			))}
			<CorridorCrowd n={num(p.zombies, 0)} f={f} s={s} />
			{darkness(light, f, 44)}
		</Svg>
	);
};

/** Inside a subway car: benches, poles, the dark tunnel in the windows. moving: lights rushing past. light: on, flicker or off (red). zombies: at the far end. */
export const Subway: React.FC<SceneProps> = ({p, f, s = 0}) => {
	const light = str(p.light, 'on');
	const on = lightLevel(light, f, 55);
	return (
		<Svg>
			<Corridor f={f} light={light === 'off' ? 'off' : light} wall="#4a5260" wall2="#444b58" floor="#2c2f36" ceiling="#3a414d" seed={55} />
			{[true, false].map((left) => (
				<g key={String(left)}>
					<polygon points={left ? '0,560 430,820 430,900 0,980' : `${W},560 650,820 650,900 ${W},980`} fill="#07090e" />
					{p.moving
						? Array.from({length: 4}, (_, i) => {
								const t = ((f * 0.04 + i / 4) % 1);
								const x = left ? lerp(430, 0, t) : lerp(650, W, t);
								return <rect key={i} x={x - 30} y={left ? lerp(840, 700, t) : lerp(840, 700, t)} width={60} height={14} fill="#ffe7a8" opacity={0.6} />;
							})
						: null}
					<polygon points={left ? '0,1240 430,960 430,1000 0,1420' : `${W},1240 650,960 650,1000 ${W},1420`} fill="#2f5b8a" />
				</g>
			))}
			{[0.15, 0.4, 0.62].map((t, i) => (
				<g key={i}>
					<line x1={lerp(150, 470, t)} y1={lerp(0, 760, t)} x2={lerp(150, 470, t)} y2={lerp(H, 1000, t)} stroke="#d6b23a" strokeWidth={lerp(14, 3, t)} />
					<line x1={W - lerp(150, 470, t)} y1={lerp(0, 760, t)} x2={W - lerp(150, 470, t)} y2={lerp(H, 1000, t)} stroke="#d6b23a" strokeWidth={lerp(14, 3, t)} />
				</g>
			))}
			<rect x={470} y={790} width={140} height={210} fill="#5a6270" />
			<rect x={495} y={810} width={90} height={80} fill="#0c0e14" />
			<CorridorCrowd n={num(p.zombies, 0)} f={f} s={s} />
			{light === 'off' ? <rect width={W} height={H} fill="#b3201d" opacity={0.18 + 0.06 * Math.sin(f / 6)} /> : null}
			<rect width={W} height={H} fill="#02030a" opacity={0.6 - 0.5 * on} />
		</Svg>
	);
};

/** The glass skybridge between Meridian Tower and Calder Tower, high over the city. cracks: the glass is breaking. zombies: on the bridge. */
export const Skybridge: React.FC<SceneProps> = ({p, f, s = 0}) => {
	const light = str(p.light, 'off');
	return (
		<Svg>
			<rect width={W} height={H} fill="url(#nightSky)" />
			<Stars frame={f} n={40} maxY={500} seed={s + 8} />
			<Skyline base={1500} seed={70 + (s % 40)} color="#0f1730" maxH={900} lit={0.1} />
			<FireGlow x={200 + hash(s) * 600} y={1500} r={300} frame={f} />
			<rect x={390} y={420} width={300} height={700} fill="#141b30" />
			{Array.from({length: 40}, (_, i) => (
				<rect key={i} x={405 + (i % 5) * 56} y={440 + Math.floor(i / 5) * 80} width={36} height={50} fill="#e8c27a" opacity={hash(i + s) < 0.3 ? 0.55 : 0.04} />
			))}
			<path d="M0 0 L430 760 L650 760 L1080 0 Z" fill="#0b0f18" opacity={0.85} />
			<path d={`M0 ${H} L430 1000 L650 1000 L${W} ${H} Z`} fill="#2a2e38" />
			<path d="M0 0 L430 760 L430 1000 L0 1920 Z" fill="#9fc4ff" opacity={0.08} />
			<path d="M1080 0 L650 760 L650 1000 L1080 1920 Z" fill="#9fc4ff" opacity={0.08} />
			{[0.15, 0.35, 0.55, 0.72].map((t, i) => (
				<g key={i} stroke="#202634" strokeWidth={lerp(18, 4, t)}>
					<line x1={lerp(0, 430, t)} y1={lerp(0, 760, t)} x2={lerp(0, 430, t)} y2={lerp(H, 1000, t)} />
					<line x1={lerp(W, 650, t)} y1={lerp(0, 760, t)} x2={lerp(W, 650, t)} y2={lerp(H, 1000, t)} />
					<line x1={lerp(0, 430, t)} y1={lerp(0, 760, t)} x2={lerp(W, 650, t)} y2={lerp(0, 760, t)} />
				</g>
			))}
			{p.cracks ? (
				<g stroke="#dbe8ff" strokeWidth={3} opacity={0.7} fill="none">
					<path d="M200 700 L260 640 L330 660 M260 640 L250 560 L300 500 M260 640 L190 600" />
					<path d="M820 900 L760 860 L700 900 M760 860 L780 780" />
				</g>
			) : null}
			<CorridorCrowd n={num(p.zombies, 0)} f={f} s={s} />
			{light === 'off' ? null : <rect width={W} height={H} fill="#fff6e0" opacity={0.05 * lightLevel(light, f, 66)} />}
		</Svg>
	);
};

/** An apartment-block lobby: mailboxes, the lift, and the glass front doors on the street. zombies: pressing on the glass. broken: the glass is cracked. light: on, flicker or off. */
export const Lobby: React.FC<SceneProps> = ({p, f, s = 0, place = 0}) => {
	const light = str(p.light, 'flicker');
	const zombies = num(p.zombies, 0);
	const tile = ['#3b3530', '#2f3a3a', '#3a3040'][place % 3];
	return (
		<Svg>
			<rect width={W} height={H} fill="#2a2e38" />
			<rect y={1300} width={W} height={620} fill={tile} />
			{Array.from({length: 8}, (_, i) => (
				<line key={i} x1={0} y1={1300 + i * 80} x2={W} y2={1300 + i * 80} stroke="#1e1c1a" strokeWidth={3} />
			))}
			<rect x={300} y={500} width={480} height={800} fill="#0d1220" />
			<rect x={300} y={500} width={480} height={800} fill="url(#nightSky)" opacity={0.7} />
			<circle cx={430} cy={700} r={160} fill="url(#warmGlow)" opacity={0.3 * flicker(f, 7, 0.8)} />
			{Array.from({length: zombies}, (_, i) => {
				const x = 340 + hash(i + s) * 400;
				const hx = x + Math.sin(f / 15 + i) * 6;
				return (
					<g key={i} opacity={0.95}>
						<Walker x={x} y={1310} h={700} frame={f} seed={i + s} eyes crawl={false} />
						<ellipse cx={hx - 30} cy={860 + i * 20} rx={18} ry={26} fill="#3a3f36" />
						<ellipse cx={hx + 40} cy={880 + i * 24} rx={18} ry={26} fill="#3a3f36" />
					</g>
				);
			})}
			<rect x={290} y={490} width={500} height={820} fill="none" stroke="#1a1d24" strokeWidth={22} />
			<rect x={532} y={490} width={16} height={820} fill="#1a1d24" />
			<rect x={300} y={500} width={480} height={800} fill="#bcd4ff" opacity={0.06} />
			{p.broken ? (
				<g stroke="#e4eeff" strokeWidth={4} opacity={0.75} fill="none">
					<path d="M420 760 L470 700 L520 720 M470 700 L455 610 M470 700 L400 690 M470 700 L500 800" />
				</g>
			) : null}
			<g>
				{Array.from({length: 24}, (_, i) => (
					<rect key={i} x={20 + (i % 4) * 62} y={560 + Math.floor(i / 4) * 92} width={54} height={80} fill="#7d6a4a" stroke="#4a3e2a" strokeWidth={3} />
				))}
			</g>
			<rect x={850} y={560} width={200} height={740} fill="#5d6570" />
			<line x1={950} y1={560} x2={950} y2={1300} stroke="#3a4048" strokeWidth={6} />
			<rect x={890} y={480} width={120} height={50} rx={6} fill="#0b0b0d" />
			{darkness(light, f, 77)}
		</Svg>
	);
};
