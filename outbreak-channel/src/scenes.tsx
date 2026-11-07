import React from 'react';
import {C, Dog, FireGlow, H, Moon, Sitter, Skyline, Smoke, Stars, TopWalker, W, Walker, clamp, flicker, hash, lerp} from './art';
import {Cabin, Elevator, Forest, Office, Tower, Truck} from './scenes2';
import {GasStation, Hospital, Lake, Lobby, School, Skybridge, Subway, Supermarket} from './scenes3';

// Every scene is an SVG drawing of the full 1080x1920 frame. `p` holds the beat's parameters (see scripts/diarycheck.py).
export type Params = Record<string, unknown>;
// s: this part's seed, so crowds and details change between parts; place: the same for every part of a story, so
// its doors, radio, lift and office stay recognisable while another story's look different
type SceneProps = {p: Params; f: number; s?: number; place?: number};

const num = (v: unknown, d: number) => (typeof v === 'number' ? v : d);
const str = (v: unknown, d: string) => (typeof v === 'string' ? v : d);
const list = (v: unknown) => (Array.isArray(v) ? (v as unknown[]).map(String) : []);

const Svg: React.FC<{children: React.ReactNode}> = ({children}) => (
	<svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: 'absolute', inset: 0}}>
		{children}
	</svg>
);

// ---------------------------------------------------------------- outside
/** Our building at night, seen from across the street. Our window (9th floor, middle) is the lit one. */
export const Building: React.FC<SceneProps> = ({p, f, s = 0}) => {
	const zombies = num(p.zombies, 0);
	const floorH = 136;
	const top = 600;
	const cols = [300, 485, 670];
	return (
		<Svg>
			<rect width={W} height={H} fill="url(#nightSky)" />
			<Stars frame={f} n={70} maxY={700} />
			<Moon x={210} y={260} r={70} />
			{p.fire ? <FireGlow x={900} y={1180} r={420} frame={f} /> : null}
			<Smoke frame={f} xs={p.fire ? [880, 140] : [140]} base={1250} />
			<Skyline base={1300} seed={3 + (s % 50)} color={C.far} maxH={520} lit={0.05} />
			<Skyline base={1500} seed={11} color={C.near} maxH={420} lit={0.04} />
			<rect x={250} y={top - 40} width={580} height={H} fill="#1a2036" />
			<rect x={240} y={top - 60} width={600} height={26} fill="#151a2c" />
			<g>
				<rect x={640} y={top - 230} width={140} height={110} rx={10} fill="#141a2b" />
				<path d={`M650 ${top - 120} L640 ${top - 60} M770 ${top - 120} L780 ${top - 60} M710 ${top - 120} L710 ${top - 60}`} stroke="#141a2b" strokeWidth={10} />
				<path d={`M330 ${top - 60} L330 ${top - 260} M300 ${top - 210} L360 ${top - 210}`} stroke="#141a2b" strokeWidth={6} />
				<circle cx={330} cy={top - 262} r={6} fill={C.red} opacity={0.4 + 0.6 * (Math.floor(f / 20) % 2)} />
			</g>
			{Array.from({length: 10}, (_, row) =>
				cols.map((x, c) => {
					const y = top + row * floorH + 22;
					const ours = row === 1 && c === 1;
					const tv = !ours && hash(row * 3 + c + 5 + s) < 0.12;
					const lit = ours && p.lit !== false;
					return (
						<g key={`${row}-${c}`}>
							<rect x={x} y={y} width={110} height={92} fill={lit ? C.warm : tv ? '#7f9bd6' : '#0c1020'} opacity={tv ? 0.25 + 0.2 * flicker(f, row + c) : 1} />
							{lit ? (
								<>
									<rect x={x} y={y} width={110} height={92} fill="url(#warmGlow)" transform={`translate(${x + 55} ${y + 46}) scale(2.6) translate(${-x - 55} ${-y - 46})`} opacity={0.5} />
									<rect x={x + 6} y={y} width={30} height={92} fill="#a8553a" opacity={0.7} />
									<rect x={x + 74} y={y} width={30} height={92} fill="#a8553a" opacity={0.7} />
								</>
							) : null}
							<rect x={x - 6} y={y + 92} width={122} height={8} fill="#11162a" />
						</g>
					);
				}),
			)}
			{Array.from({length: zombies}, (_, i) => (
				<Walker key={i} x={((hash(i + 3) * 1300 + f * (0.4 + hash(i) * 0.4)) % 1300) - 110} y={1905 - hash(i + 9) * 30} h={110} frame={f} seed={i + s} flip={i % 2 === 1} />
			))}
		</Svg>
	);
};

/** Looking down at the street from the 9th floor window: the road, cars and the infected from above. */
export const WindowView: React.FC<SceneProps> = ({p, f, s = 0}) => {
	const zombies = num(p.zombies, 4);
	const cars: [number, number, number, string][] = [
		[160, 820, 8, '#3b4a63'],
		[520, 1130, -6, '#5a2f33'],
		[860, 860, 4, '#2f4a45'],
		[300, 1220, 90, '#4a4a52'],
	];
	return (
		<Svg>
			<rect width={W} height={H} fill="#10131c" />
			<rect x={0} y={0} width={W} height={560} fill="#191d28" />
			<rect x={0} y={1460} width={W} height={460} fill="#191d28" />
			<rect x={0} y={560} width={W} height={18} fill="#262b38" />
			<rect x={0} y={1442} width={W} height={18} fill="#262b38" />
			{Array.from({length: 12}, (_, i) => (
				<rect key={i} x={i * 100 + 20} y={1000} width={56} height={10} fill="#8d8f86" opacity={0.35} />
			))}
			{Array.from({length: 7}, (_, i) => (
				<rect key={`z${i}`} x={60 + i * 34} y={600} width={18} height={820} fill="#cfd2c8" opacity={0.12} />
			))}
			{[
				[250, 520, 0],
				[830, 1500, 1],
			].map(([x, y, k]) => (
				<g key={k}>
					<circle cx={x} cy={y} r={300} fill="url(#warmGlow)" opacity={0.35 * (k ? flicker(f, 4, 0.7) : 1)} />
					<circle cx={x} cy={y} r={14} fill="#3a3a3a" />
				</g>
			))}
			{cars.map(([x, y, rot, color], i) => (
				<g key={i} transform={`translate(${(x + hash(i + s) * 260) % 1000} ${y}) rotate(${rot + (hash(i + s + 9) - 0.5) * 30})`}>
					<rect x={-115} y={-55} width={230} height={110} rx={30} fill={color} />
					<rect x={-60} y={-44} width={110} height={88} rx={16} fill="#11151f" opacity={0.85} />
					<rect x={46} y={-44} width={26} height={88} rx={8} fill="#2a3346" />
					{i === 1 && p.fire ? null : <rect x={-110} y={-40} width={8} height={20} fill="#ff9a2e" opacity={Math.floor(f / 15) % 2 ? 0.9 : 0.2} />}
				</g>
			))}
			{p.fire ? (
				<>
					<FireGlow x={520} y={1130} r={260} frame={f} />
					<Smoke frame={f} xs={[520]} base={1150} color="#1c1e24" />
				</>
			) : null}
			{Array.from({length: zombies}, (_, i) => {
				const x0 = hash(i + 20 + s) * 1000 + 40;
				const y0 = 640 + hash(i + 31 + s) * 760;
				const dx = Math.sin(f / (90 + i * 7) + i) * 30 + f * 0.15 * (hash(i) - 0.5);
				return <TopWalker key={i} x={x0 + dx} y={y0 + Math.cos(f / 70 + i) * 14} s={1.7} frame={f} seed={i + s} />;
			})}
			{p.survivor ? (
				<g transform={`translate(${-120 + ((f * 9) % 1400)} 980)`}>
					<ellipse cx={0} cy={0} rx={24} ry={11} fill="#c9c2b2" />
					<circle cx={8} cy={0} r={9} fill="#7a5a48" />
					<path d="M20 0 L320 -60 L320 60 Z" fill="#fff6d0" opacity={0.15} />
				</g>
			) : null}
			<g>
				<rect x={0} y={0} width={W} height={110} fill="#1b1f2c" />
				<rect x={0} y={1810} width={W} height={110} fill="#1b1f2c" />
				<rect x={0} y={0} width={80} height={H} fill="#1b1f2c" />
				<rect x={W - 80} y={0} width={80} height={H} fill="#1b1f2c" />
				<rect x={520} y={0} width={40} height={H} fill="#1b1f2c" />
				<rect x={0} y={940} width={W} height={36} fill="#1b1f2c" />
				<rect x={80} y={110} width={W - 160} height={1700} fill="none" stroke="#2a3042" strokeWidth={10} />
			</g>
			{Array.from({length: 26}, (_, i) => {
				const x = 100 + hash(i + 70) * 880;
				const y = (hash(i + 90) * 1700 + f * (0.6 + hash(i) * 1.6)) % 1700 + 110;
				return <ellipse key={`d${i}`} cx={x} cy={y} rx={5} ry={8} fill="#cfe0ff" opacity={0.18} />;
			})}
		</Svg>
	);
};

/** Street level, looking down the road to the harbour. */
export const Street: React.FC<SceneProps> = ({p, f, s = 0}) => {
	const zombies = num(p.zombies, 3);
	const hz = 1000;
	return (
		<Svg>
			<rect width={W} height={H} fill="url(#nightSky)" />
			<Stars frame={f} n={40} maxY={600} seed={9} />
			<Skyline base={hz} seed={21 + (s % 50)} color={C.far} maxH={340} lit={0.04} />
			{p.fire ? <FireGlow x={760} y={hz - 60} r={360} frame={f} /> : null}
			<Smoke frame={f} xs={[760, 240]} base={hz} />
			<path d={`M0 ${hz - 520} L340 ${hz - 120} L340 ${hz + 40} L0 ${H}`} fill="#121828" />
			<path d={`M${W} ${hz - 600} L740 ${hz - 130} L740 ${hz + 40} L${W} ${H}`} fill="#101626" />
			{[0.15, 0.35, 0.55, 0.72].map((t, i) => (
				<g key={i}>
					<rect x={lerp(20, 330, t)} y={lerp(hz - 420, hz - 100, t)} width={lerp(90, 14, t)} height={lerp(110, 18, t)} fill={i === 1 ? '#e8b35f' : '#0b0f1c'} opacity={i === 1 ? 0.35 * flicker(f, 2) : 1} />
					<rect x={W - lerp(110, 344, t)} y={lerp(hz - 480, hz - 105, t)} width={lerp(90, 14, t)} height={lerp(110, 18, t)} fill="#0b0f1c" />
				</g>
			))}
			<path d={`M340 ${hz + 40} L740 ${hz + 40} L${W + 500} ${H} L-500 ${H} Z`} fill="#1a1d27" />
			<path d={`M520 ${hz + 40} L560 ${hz + 40} L640 ${H} L440 ${H} Z`} fill="#2a2d36" opacity={0.6} />
			{[0, 1, 2, 3, 4].map((k) => {
				const t = k / 5;
				const y = lerp(hz + 60, H, t * t);
				return <rect key={k} x={536 - lerp(3, 26, t)} y={y} width={lerp(6, 52, t)} height={lerp(10, 90, t)} fill="#c9c6b4" opacity={0.3} />;
			})}
			<g transform="translate(150 1480)">
				<path d="M0 0 L40 -90 L200 -120 L330 -110 L410 -40 L430 0 Z" fill="#2c3448" />
				<path d="M70 -86 L190 -112 L300 -104 L360 -46 L60 -40 Z" fill="#0d111b" />
				<circle cx={90} cy={0} r={48} fill="#0a0c12" />
				<circle cx={340} cy={0} r={48} fill="#0a0c12" />
				<circle cx={418} cy={-30} r={14} fill="#ffad33" opacity={Math.floor(f / 14) % 2 ? 0.95 : 0.15} />
				<circle cx={418} cy={-30} r={70} fill="url(#fireGlow)" opacity={Math.floor(f / 14) % 2 ? 0.5 : 0} />
			</g>
			<g transform="translate(860 1620) rotate(80)">
				<rect x={-60} y={-90} width={120} height={180} rx={14} fill="#2f3a3a" />
			</g>
			{Array.from({length: zombies}, (_, i) => {
				const depth = 0.25 + hash(i + 4 + s) * 0.75;
				const y = lerp(hz + 60, 1880, depth);
				const h = lerp(120, 560, depth);
				const dir = hash(i + 8) < 0.5 ? 1 : -1;
				const x = ((hash(i + 6) * 1400 + f * dir * (0.3 + depth * 0.8)) % 1400 + 1400) % 1400 - 160;
				const color = depth < 0.45 ? '#232a3d' : depth < 0.7 ? '#131722' : C.ink;  // far ones fade into the fog
				return <Walker key={i} x={x} y={y} h={h} frame={f} seed={i + s} flip={dir < 0} eyes={depth > 0.6} color={color} />;
			})}
			<rect x={0} y={hz - 120} width={W} height={300} fill="#3a4258" opacity={0.18} filter="url(#blur24)" />
		</Svg>
	);
};

/** The roof: water tank, antenna, and the city burning on the horizon. */
export const Rooftop: React.FC<SceneProps> = ({p, f, s = 0}) => {
	const heliX = -300 + ((f * 4) % 1800);
	return (
		<Svg>
			<rect width={W} height={H} fill="url(#nightSky)" />
			<Stars frame={f} n={70} maxY={800} seed={4} />
			<Moon x={860} y={280} r={56} />
			{p.fire !== false ? (
				<>
					<FireGlow x={150 + hash(s) * 400} y={1150} r={380} frame={f} />
					<FireGlow x={650 + hash(s + 1) * 350} y={1180} r={260} frame={f + 20} />
				</>
			) : null}
			<Smoke frame={f} xs={[300, 880, 600]} base={1150} />
			<Skyline base={1250} seed={31 + (s % 50)} color={C.far} maxH={380} lit={0.05} />
			{p.heli ? (
				<g transform={`translate(${heliX} 430)`}>
					<path d={`M0 0 L-${260} 820 L${260} 820 Z`} fill="#fff7d6" opacity={0.08} transform={`rotate(${Math.sin(f / 30) * 18})`} />
					<ellipse cx={0} cy={0} rx={60} ry={22} fill="#0b0d14" />
					<rect x={40} y={-6} width={90} height={10} fill="#0b0d14" />
					<rect x={-70} y={-30} width={140} height={4} fill="#0b0d14" />
					<circle cx={-50} cy={6} r={5} fill={C.red} opacity={Math.floor(f / 10) % 2 ? 1 : 0.2} />
				</g>
			) : null}
			<rect x={0} y={1300} width={W} height={620} fill="#20232d" />
			<rect x={0} y={1280} width={W} height={40} fill="#2b2f3b" />
			{Array.from({length: 40}, (_, i) => (
				<circle key={i} cx={hash(i + 5) * W} cy={1340 + hash(i + 9) * 560} r={3 + hash(i) * 3} fill="#2c303b" />
			))}
			<g transform="translate(90 760)">
				<rect x={20} y={0} width={260} height={330} rx={24} fill="#141823" />
				<rect x={20} y={60} width={260} height={10} fill="#1d2230" />
				<rect x={20} y={200} width={260} height={10} fill="#1d2230" />
				<path d="M40 330 L20 540 M260 330 L280 540 M150 330 L150 540" stroke="#141823" strokeWidth={14} />
			</g>
			<path d="M860 1280 L860 860 M820 940 L900 940 M830 1010 L890 1010" stroke="#141823" strokeWidth={8} />
			<rect x={600} y={1420} width={160} height={110} fill="#191c26" />
			{p.flare ? (
				<g>
					<circle cx={520} cy={1600} r={260} fill="#ff2a2a" opacity={0.18 + 0.05 * Math.sin(f / 2)} filter="url(#blur24)" />
					<rect x={512} y={1560} width={14} height={60} fill="#c22" transform="rotate(25 520 1600)" />
					<circle cx={530} cy={1570} r={10} fill="#ffd1c8" />
				</g>
			) : null}
		</Svg>
	);
};

// ---------------------------------------------------------------- inside
/** Our living room. light: lamp, off or candle. dog: none, lie, sleep, sit, alert. guest: okafor or leo on the couch. */
export const Room: React.FC<SceneProps> = ({p, f}) => {
	const light = str(p.light, 'lamp');
	const lamp = light === 'lamp' ? 0.92 + 0.08 * Math.sin(f / 9) * (hash(Math.floor(f / 4)) > 0.9 ? 3 : 1) : 0;
	const lit = light === 'lamp' ? 1 : light === 'candle' ? 0.55 : 0.25;
	const dog = str(p.dog, 'lie');
	const guest = str(p.guest, '');
	return (
		<Svg>
			<rect width={W} height={1380} fill={C.wall} />
			<rect y={1380} width={W} height={540} fill={C.floor} />
			<rect y={1370} width={W} height={18} fill="#1a1d2b" />
			<g>
				<rect x={330} y={300} width={420} height={600} fill="url(#nightSky)" />
				<Moon x={640} y={420} r={34} />
				<Skyline base={900} seed={8} color={C.far} maxH={260} lit={0.06} />
				{p.boarded ? (
					<g fill="#5a4330">
						<rect x={300} y={380} width={480} height={56} transform="rotate(-8 540 408)" />
						<rect x={300} y={600} width={480} height={56} transform="rotate(5 540 628)" />
						<rect x={300} y={800} width={480} height={56} transform="rotate(-4 540 828)" />
					</g>
				) : null}
				<rect x={330} y={300} width={420} height={600} fill="none" stroke="#3a3f55" strokeWidth={22} />
				<rect x={530} y={300} width={20} height={600} fill="#3a3f55" />
				<path d={`M290 270 Q${300 + Math.sin(f / 40) * 6} 600 280 940 L360 940 Q340 600 350 270 Z`} fill="#5a2d34" />
				<path d={`M790 270 Q${780 + Math.sin(f / 37) * 6} 600 800 940 L720 940 Q740 600 730 270 Z`} fill="#5a2d34" />
				<rect x={270} y={262} width={540} height={16} rx={8} fill="#1f2230" />
			</g>
			{light !== 'lamp' ? <path d="M330 900 L750 900 L980 1920 L120 1920 Z" fill="#a9c4ff" opacity={0.05} /> : null}
			<rect x={110} y={430} width={150} height={190} fill="#1c2030" stroke="#4a4436" strokeWidth={10} />
			<ellipse cx={560} cy={1660} rx={420} ry={120} fill="#33283c" />
			<g>
				<rect x={80} y={1060} width={600} height={220} rx={40} fill="#22414a" />
				<rect x={60} y={1220} width={640} height={170} rx={30} fill="#2a4d57" />
				<rect x={40} y={1150} width={90} height={260} rx={30} fill="#1f3c44" />
				<rect x={630} y={1150} width={90} height={260} rx={30} fill="#1f3c44" />
				<rect x={90} y={1390} width={20} height={40} fill="#14161f" />
				<rect x={650} y={1390} width={20} height={40} fill="#14161f" />
			</g>
			{guest ? <Sitter x={300} y={1240} s={1.15} frame={f} who={guest} /> : null}
			<g>
				<rect x={740} y={1250} width={170} height={150} fill="#2a2320" />
				<rect x={760} y={1190} width={120} height={60} rx={8} fill="#3d3530" />
				<circle cx={850} cy={1220} r={14} fill={light === 'off' ? '#3a2a14' : '#e0a540'} opacity={0.8} />
			</g>
			<g>
				<rect x={966} y={760} width={12} height={640} fill="#191b24" />
				<path d="M900 640 L1040 640 L1010 760 L930 760 Z" fill={lamp ? '#f1c27a' : '#3b3430'} />
				<rect x={930} y={1394} width={80} height={14} rx={7} fill="#191b24" />
			</g>
			{light === 'candle' ? (
				<g>
					<rect x={792} y={1150} width={22} height={44} fill="#e8e2d0" />
					<ellipse cx={803} cy={1136 + Math.sin(f / 3) * 2} rx={9} ry={18} fill="#ffcf6b" />
				</g>
			) : null}
			{dog !== 'none' ? <Dog x={600} y={1690} s={1.25} frame={f} pose={dog} light={lit} /> : null}
			{light === 'lamp' ? <circle cx={970} cy={760} r={900} fill="url(#warmGlow)" opacity={0.45 * lamp} /> : null}
			{light === 'candle' ? <circle cx={803} cy={1140} r={600} fill="url(#warmGlow)" opacity={0.42 + 0.06 * Math.sin(f / 2.7)} /> : null}
			<rect width={W} height={H} fill="#03050c" opacity={light === 'lamp' ? 0.12 : light === 'candle' ? 0.42 : 0.6} />
		</Svg>
	);
};

/** The inside of our front door. shadow: feet moving in the light under the door. banging: someone pounding. */
const DOORS = [[C.wood, C.wood2], ['#2f4a3a', '#243a2d'], ['#5a2a2a', '#452020'], ['#4a4f58', '#3b3f47']];

export const Door: React.FC<SceneProps> = ({p, f, place = 0}) => {
	const [door, panel] = DOORS[place % DOORS.length];
	const bang = p.banging ? Math.max(0, Math.sin(f * 0.55)) ** 8 : 0;
	const feetX = 470 + Math.sin(f / 22) * 40;
	return (
		<Svg>
			<rect width={W} height={H} fill="#1d2130" />
			<rect y={1770} width={W} height={150} fill="#101219" />
			<rect x={200} y={210} width={680} height={1570} fill="#151823" />
			<g transform={`translate(${bang * 6} ${bang * -3}) rotate(${bang * 0.4} 540 1000)`}>
				<rect x={230} y={240} width={620} height={1512} fill={door} />
				<rect x={290} y={310} width={500} height={560} rx={10} fill={panel} />
				<rect x={290} y={960} width={500} height={700} rx={10} fill={panel} />
				<circle cx={540} cy={640} r={16} fill="#8c7350" />
				<circle cx={540} cy={640} r={7} fill="#0b0b0b" />
				<rect x={760} y={960} width={60} height={110} rx={12} fill="#8c7350" />
				<circle cx={790} cy={1040} r={24} fill="#a88a5c" />
				<rect x={772} y={860} width={40} height={60} rx={8} fill="#8c7350" />
				{Array.from({length: 9}, (_, i) => (
					<ellipse key={i} cx={858 + i * 9 + Math.sin(f / 7 + i) * bang * 6} cy={800 + i * 14 + Math.sin(i * 1.4) * 10} rx={7} ry={4} fill="none" stroke="#9a9a9a" strokeWidth={3} />
				))}
			</g>
			<rect x={230} y={1752} width={620} height={10} fill="#ffdca0" opacity={0.55} />
			<rect x={230} y={1756} width={620} height={60} fill="url(#warmGlow)" opacity={0.25} />
			{p.shadow ? (
				<>
					<rect x={feetX - 70} y={1750} width={60} height={14} fill="#0b0b0f" />
					<rect x={feetX + 30} y={1750} width={60} height={14} fill="#0b0b0f" />
				</>
			) : null}
			{p.banging
				? Array.from({length: 14}, (_, i) => {
						const t = ((f * 3 + i * 23) % 120) / 120;
						return <circle key={i} cx={240 + hash(i) * 600} cy={220 + t * 400} r={2 + hash(i + 3) * 2} fill="#c9c0aa" opacity={0.5 * (1 - t) * (bang > 0.05 ? 1 : 0.4)} />;
					})
				: null}
			<rect width={W} height={H} fill="#03050c" opacity={0.35} />
		</Svg>
	);
};

/** Looking through the peephole. who: okafor, leo, zombie or empty. */
export const Peephole: React.FC<SceneProps> = ({p, f}) => {
	const who = str(p.who, 'empty');
	const sway = Math.sin(f / 20) * 10;
	const lightOn = flicker(f, 7, 0.9);
	return (
		<Svg>
			<rect width={W} height={H} fill="#000" />
			<defs>
				<clipPath id="eye">
					<circle cx={540} cy={900} r={420} />
				</clipPath>
				<radialGradient id="lens">
					<stop offset="60%" stopColor="#000" stopOpacity={0} />
					<stop offset="100%" stopColor="#000" stopOpacity={0.95} />
				</radialGradient>
			</defs>
			<g clipPath="url(#eye)">
				<rect x={100} y={460} width={880} height={880} fill="#3b3f4a" opacity={0.6 + 0.4 * lightOn} />
				<path d="M100 460 L420 760 L660 760 L980 460 Z" fill="#2a2e38" />
				<path d="M100 1340 L420 1040 L660 1040 L980 1340 Z" fill="#2c2721" />
				<rect x={420} y={760} width={240} height={280} fill="#14161c" />
				<rect x={490} y={720} width={100} height={28} fill="#2bd46b" opacity={0.6} />
				{who === 'okafor' || who === 'leo' ? (
					<g transform={`translate(${540 + sway} 1300)`}>
						<path d="M-260 0 Q-250 -260 -120 -330 L120 -330 Q250 -260 260 0 Z" fill={who === 'leo' ? '#2e3f5e' : '#5b3f52'} />
						<ellipse cx={0} cy={-470} rx={130} ry={160} fill="#7a5040" />
						{who === 'okafor' ? (
							<path d="M-135 -480 Q-120 -650 0 -640 Q130 -650 135 -480 Q90 -560 -135 -480 Z" fill="#b9b6b0" />
						) : (
							<path d="M-150 -450 Q-170 -680 0 -670 Q170 -680 150 -450 L120 -400 Q0 -640 -120 -400 Z" fill="#2e3f5e" />
						)}
						<ellipse cx={-48} cy={-470} rx={14} ry={10} fill="#1a1010" />
						<ellipse cx={48} cy={-470} rx={14} ry={10} fill="#1a1010" />
						<path d="M-40 -390 Q0 -405 40 -390" stroke="#3a2420" strokeWidth={8} fill="none" />
					</g>
				) : null}
				{who === 'zombie' ? (
					<g transform={`translate(${540 + sway * 2} 1320) rotate(${-8 + Math.sin(f / 15) * 4})`}>
						<path d="M-260 0 Q-250 -260 -120 -330 L120 -330 Q250 -260 260 0 Z" fill="#0b0c10" />
						<ellipse cx={0} cy={-480} rx={140} ry={165} fill="#0b0c10" />
						<circle cx={-50} cy={-480} r={10} fill="#e6eed0" opacity={0.9} />
						<circle cx={50} cy={-476} r={9} fill="#e6eed0" opacity={0.8} />
					</g>
				) : null}
				<circle cx={540} cy={900} r={420} fill="url(#lens)" />
			</g>
			<circle cx={540} cy={900} r={430} fill="none" stroke="#5c4a30" strokeWidth={22} />
		</Svg>
	);
};

/** The 9th floor corridor. light: on, flicker or off. zombie: a figure at the far end that gets closer. */
export const Hallway: React.FC<SceneProps> = ({p, f, s = 0}) => {
	const light = str(p.light, 'flicker');
	const vx0 = 420;
	const vx1 = 660;
	const vy0 = 700;
	const vy1 = 960;
	const on = light === 'on' ? 1 : light === 'off' ? 0.08 : flicker(f, 3, 0.7);
	const side = (t: number, left: boolean) => {
		const x = left ? lerp(0, vx0, t) : lerp(W, vx1, t);
		return {x, top: lerp(0, vy0, t), bot: lerp(H, vy1, t)};
	};
	const doors = [0.18, 0.45, 0.66];
	const z = p.zombie ? clamp(f / 240) : 0;
	return (
		<Svg>
			<path d={`M0 0 L${W} 0 L${vx1} ${vy0} L${vx0} ${vy0} Z`} fill="#1b1e29" />
			<path d={`M0 ${H} L${W} ${H} L${vx1} ${vy1} L${vx0} ${vy1} Z`} fill="#231d1d" />
			<path d={`M${W / 2 - 220} ${H} L${W / 2 + 220} ${H} L${560} ${vy1} L${520} ${vy1} Z`} fill="#3a1f24" opacity={0.7} />
			<path d={`M0 0 L${vx0} ${vy0} L${vx0} ${vy1} L0 ${H} Z`} fill="#2b3040" />
			<path d={`M${W} 0 L${vx1} ${vy0} L${vx1} ${vy1} L${W} ${H} Z`} fill="#262a39" />
			<rect x={vx0} y={vy0} width={vx1 - vx0} height={vy1 - vy0} fill="#0a0b10" />
			<rect x={490} y={vy0 - 40} width={100} height={30} fill="#2bd46b" opacity={0.75} />
			<circle cx={540} cy={vy0 - 25} r={80} fill="#2bd46b" opacity={0.12} />
			{doors.map((t, i) =>
				[true, false].map((left) => {
					const a = side(t, left);
					const b = side(t + 0.1, left);
					const top = (s: {top: number; bot: number}) => lerp(s.top, s.bot, 0.18);
					const pts = `${a.x},${top(a)} ${b.x},${top(b)} ${b.x},${b.bot} ${a.x},${a.bot}`;
					return <polygon key={`${i}${left}`} points={pts} fill="#3a2b22" stroke="#171820" strokeWidth={6} />;
				}),
			)}
			{[0.08, 0.3, 0.52, 0.72].map((t, i) => {
				const y = lerp(0, vy0, t) + 10;
				const w = lerp(260, 50, t);
				const o = light === 'flicker' ? flicker(f, i * 5 + 1, 0.75) : on;
				return (
					<g key={i}>
						<rect x={540 - w / 2} y={y} width={w} height={lerp(26, 6, t)} fill="#f5f0dc" opacity={0.2 + 0.8 * o} />
						<ellipse cx={540} cy={y + 40} rx={w * 1.4} ry={lerp(160, 40, t)} fill="#fff3d6" opacity={0.12 * o} />
					</g>
				);
			})}
			{p.zombie ? <Walker x={540} y={lerp(vy1 - 6, 1500, z * z)} h={lerp(230, 900, z * z)} frame={f} seed={2 + s} eyes crawl={false} /> : null}
			<rect width={W} height={H} fill="#02030a" opacity={0.75 - 0.55 * on} />
		</Svg>
	);
};

/** Looking down the stairwell, nine floors to the bottom. zombies: shapes moving far below. */
export const Stairwell: React.FC<SceneProps> = ({p, f, place = 0}) => {
	const rail = ['#7c3b2c', '#8a7a2c', '#2c6a4a', '#5a5f6a'][place % 4];
	const rings = 9;
	return (
		<Svg>
			<rect width={W} height={H} fill="#07080d" />
			<g transform={`rotate(${Math.sin(f / 60) * 1.5} 540 960)`}>
				{Array.from({length: rings}, (_, i) => {
					const t = i / rings;
					const x = lerp(-60, 400, t);
					const y = lerp(-120, 820, t);
					const w = W - 2 * x;
					const h = 1920 - 2 * y + lerp(120, -80, t);
					const shade = Math.round(lerp(64, 12, t));
					return (
						<g key={i}>
							<rect x={x} y={y} width={w} height={h} fill={`rgb(${shade},${shade + 3},${shade + 10})`} />
							<rect x={x} y={y} width={w} height={h} fill="none" stroke={rail} strokeWidth={lerp(22, 4, t)} />
							{i < rings - 1 ? (
								<text x={x + lerp(60, 14, t)} y={y + lerp(140, 30, t)} fill="#c9c4b4" opacity={0.5 - t * 0.4} fontSize={lerp(110, 20, t)} fontFamily="monospace">
									{9 - i}
								</text>
							) : null}
						</g>
					);
				})}
				<rect x={430} y={850} width={220} height={190} fill="#000" />
				{p.zombies
					? Array.from({length: 5}, (_, i) => (
							<g key={i} transform={`translate(${470 + hash(i) * 140 + Math.sin(f / 20 + i) * 8} ${880 + hash(i + 3) * 120})`}>
								<circle r={10} fill="#1a1c22" />
								<path d={`M-6 4 L-14 ${-20 - Math.sin(f / 9 + i) * 6} M6 4 L14 ${-18 - Math.cos(f / 9 + i) * 6}`} stroke="#22252c" strokeWidth={5} strokeLinecap="round" />
							</g>
						))
					: null}
			</g>
		</Svg>
	);
};

/** The kitchen. power: fridge open and lit (true) or dark (false). cans: tins left on the counter. */
export const Kitchen: React.FC<SceneProps> = ({p, f}) => {
	const power = p.power !== false;
	const cans = num(p.cans, 3);
	const drip = (f % 45) / 45;
	return (
		<Svg>
			<rect width={W} height={H} fill="#22283a" />
			{Array.from({length: 12}, (_, i) => (
				<line key={i} x1={0} y1={640 + i * 44} x2={720} y2={640 + i * 44} stroke="#2c3346" strokeWidth={3} />
			))}
			<rect x={40} y={300} width={300} height={320} fill="#2e2620" />
			<rect x={360} y={300} width={300} height={320} fill="#2e2620" />
			<path d="M360 300 L250 340 L250 590 L360 620 Z" fill="#3a3028" />
			<rect x={30} y={1140} width={700} height={70} fill="#4a4740" />
			<rect x={30} y={1210} width={700} height={520} fill="#2a231e" />
			<rect x={80} y={1270} width={280} height={400} fill="#241d18" />
			<rect x={400} y={1270} width={280} height={400} fill="#241d18" />
			<rect x={440} y={1100} width={200} height={40} rx={10} fill="#6b6e75" />
			<path d="M600 1100 Q600 1020 540 1020" stroke="#8a8d94" strokeWidth={14} fill="none" />
			<ellipse cx={540} cy={1040 + drip * 70} rx={6} ry={9} fill="#9fc3ff" opacity={1 - drip * 0.5} />
			{Array.from({length: cans}, (_, i) => (
				<g key={i} transform={`translate(${90 + i * 82} 1050)`}>
					<rect width={64} height={90} rx={8} fill="#8b8f96" />
					<rect y={22} width={64} height={46} fill={['#a33', '#3a6', '#c83', '#36a', '#a3a', '#888'][i % 6]} />
					<ellipse cx={32} cy={0} rx={32} ry={8} fill="#b0b4bb" />
				</g>
			))}
			<g>
				<rect x={760} y={520} width={290} height={1210} rx={20} fill="#c9ccd2" />
				{power ? (
					<>
						<rect x={780} y={540} width={250} height={1170} fill="#eef3ff" />
						{[760, 1000, 1240].map((y) => (
							<rect key={y} x={780} y={y} width={250} height={8} fill="#c8d2e6" />
						))}
						<rect x={810} y={1190} width={50} height={46} rx={6} fill="#e8d6a0" />
						<path d="M760 540 L560 610 L560 1660 L760 1710 Z" fill="#b6b9c0" />
						<circle cx={900} cy={1100} r={800} fill="url(#coolGlow)" opacity={0.6} />
					</>
				) : (
					<>
						<rect x={760} y={520} width={290} height={8} fill="#9fa3ab" />
						<rect x={1000} y={700} width={14} height={220} rx={6} fill="#9fa3ab" />
					</>
				)}
			</g>
			<rect width={W} height={H} fill="#03050c" opacity={power ? 0.3 : 0.55} />
		</Svg>
	);
};

// ---------------------------------------------------------------- close-ups
/** A hand holding a phone. screen: alert, message, nosignal or battery. lines: the text on screen. */
export const Phone: React.FC<SceneProps> = ({p, f}) => {
	const screen = str(p.screen, 'alert');
	const lines = list(p.lines);
	const battery = num(p.battery, 40);
	const sx = 290;
	const sw = 500;
	return (
		<div style={{position: 'absolute', inset: 0, background: 'radial-gradient(circle at 50% 45%, #1d2438 0%, #07090f 70%)'}}>
			<div style={{position: 'absolute', left: 250, top: 330, width: 580, height: 1240, borderRadius: 80, background: '#0b0c10', boxShadow: '0 0 160px rgba(140,170,255,0.25)'}} />
			<div style={{position: 'absolute', left: sx, top: 380, width: sw, height: 1140, borderRadius: 54, overflow: 'hidden', background: screen === 'alert' ? '#1b0e10' : '#0f131c', fontFamily: 'Inter, sans-serif'}}>
				<div style={{display: 'flex', justifyContent: 'space-between', padding: '26px 34px', color: '#cfd6e6', fontSize: 30}}>
					<span>{screen === 'nosignal' || screen === 'battery' ? 'No Service' : '03:12'}</span>
					<span style={{color: battery <= 20 ? C.red : '#cfd6e6'}}>{battery}%</span>
				</div>
				{screen === 'alert' ? (
					<div style={{margin: '80px 26px', background: '#2a1215', borderRadius: 30, padding: 34, border: `3px solid ${C.red}`}}>
						<div style={{color: C.red, fontSize: 40, fontWeight: 800, letterSpacing: 2}}>EMERGENCY ALERT</div>
						{lines.map((l, i) => (
							<div key={i} style={{color: '#f3e9e9', fontSize: 38, lineHeight: 1.3, marginTop: 22, opacity: clamp((f - 10 - i * 12) / 8)}}>
								{l}
							</div>
						))}
					</div>
				) : null}
				{screen === 'message' ? (
					<div style={{padding: '30px 26px'}}>
						<div style={{color: '#9fb0d0', fontSize: 32, textAlign: 'center', marginBottom: 40}}>{lines[0] ?? ''}</div>
						{lines.slice(1).map((l, i) => (
							<div key={i} style={{background: '#273145', color: '#eef2fa', fontSize: 36, borderRadius: 30, padding: '20px 28px', margin: '18px 60px 18px 0', opacity: clamp((f - 8 - i * 14) / 8)}}>
								{l}
							</div>
						))}
					</div>
				) : null}
				{screen === 'nosignal' || screen === 'battery' ? (
					<div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: 260, color: '#cfd6e6'}}>
						{screen === 'nosignal' ? (
							<svg width={220} height={180} viewBox="0 0 220 180">
								{[0, 1, 2, 3].map((i) => (
									<rect key={i} x={20 + i * 50} y={140 - i * 40} width={34} height={40 + i * 40} rx={6} fill="#3a4258" />
								))}
								<path d="M120 20 L200 100 M200 20 L120 100" stroke={C.red} strokeWidth={14} strokeLinecap="round" />
							</svg>
						) : (
							<svg width={300} height={150} viewBox="0 0 300 150">
								<rect x={10} y={10} width={250} height={130} rx={20} fill="none" stroke="#cfd6e6" strokeWidth={10} />
								<rect x={262} y={50} width={24} height={50} rx={6} fill="#cfd6e6" />
								<rect x={26} y={26} width={(218 * battery) / 100} height={98} rx={10} fill={battery <= 20 ? C.red : '#5fd17a'} opacity={0.6 + 0.4 * Math.abs(Math.sin(f / 10))} />
							</svg>
						)}
						<div style={{fontSize: 40, marginTop: 40}}>{lines[0] ?? (screen === 'nosignal' ? 'Searching...' : 'Battery low')}</div>
					</div>
				) : null}
			</div>
			<svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
				<path d="M150 1920 L190 1380 Q200 1260 290 1240 L330 1250 L320 1420 Q300 1520 360 1600 L420 1920 Z" fill="#6a4a3c" />
				<path d="M800 1180 Q860 1170 880 1230 L880 1330 Q860 1370 800 1360 Z" fill="#5f4236" />
				<path d="M790 1380 Q860 1370 880 1430 L880 1520 Q860 1560 790 1550 Z" fill="#5f4236" />
			</svg>
		</div>
	);
};

/** An old portable radio. mode: static or voice. */
const RADIOS = [['#3b2e26', '#4a3a2f'], ['#6e2420', '#8a2e28'], ['#2f3a2a', '#3d4a35'], ['#2a2d33', '#3a3e46']];

export const Radio: React.FC<SceneProps> = ({p, f, place = 0}) => {
	const [shell, face] = RADIOS[place % RADIOS.length];
	const voice = str(p.mode, 'static') === 'voice';
	const needle = voice ? 610 : 560 + Math.sin(f / 6) * 50 + Math.sin(f / 2.3) * 12;
	return (
		<Svg>
			<rect width={W} height={H} fill="#0d0f16" />
			<rect y={1240} width={W} height={680} fill="#2a2019" />
			<circle cx={540} cy={1000} r={700} fill="url(#warmGlow)" opacity={0.18} />
			<g transform="translate(140 700)">
				<rect x={0} y={0} width={800} height={540} rx={50} fill={shell} />
				<rect x={20} y={20} width={760} height={500} rx={40} fill={face} />
				<path d="M160 0 Q400 -200 640 0" stroke="#2a201b" strokeWidth={24} fill="none" />
				<circle cx={230} cy={290} r={170} fill="#2a211c" />
				{Array.from({length: 11}, (_, r) =>
					Array.from({length: 11}, (_, c) => {
						const x = 100 + c * 26;
						const y = 160 + r * 26;
						return (x - 230) ** 2 + (y - 290) ** 2 < 150 ** 2 ? <circle key={`${r}-${c}`} cx={x} cy={y} r={7} fill="#15110e" /> : null;
					}),
				)}
				<rect x={440} y={110} width={290} height={140} rx={16} fill={voice ? '#f0b44a' : '#c98a32'} opacity={0.65 + 0.35 * (voice ? 1 : flicker(f, 9, 0.8))} />
				{Array.from({length: 9}, (_, i) => (
					<rect key={i} x={460 + i * 30} y={130} width={4} height={i % 2 ? 22 : 36} fill="#3a2610" />
				))}
				<rect x={needle - 140} y={120} width={6} height={120} fill={C.red} />
				<circle cx={500} cy={380} r={56} fill="#2a211c" />
				<circle cx={670} cy={380} r={56} fill="#2a211c" />
				<rect x={496} y={330} width={8} height={40} fill="#c9b48a" transform={`rotate(${f * 0.5} 500 380)`} />
			</g>
			{voice
				? [0, 1, 2].map((i) => {
						const t = ((f + i * 15) % 45) / 45;
						return <circle key={i} cx={370} cy={990} r={180 + t * 260} fill="none" stroke="#f0c070" strokeWidth={6} opacity={0.4 * (1 - t)} />;
					})
				: Array.from({length: 18}, (_, i) => (
						<rect key={i} x={hash(i + Math.floor(f / 2)) * W} y={hash(i * 3 + Math.floor(f / 2)) * H} width={60 + hash(i) * 200} height={3} fill="#c9d1e0" opacity={0.08} />
					))}
		</Svg>
	);
};

const ITEM_COLORS: Record<string, string> = {water: '#5aa9e6', can: '#a33', dogfood: '#c8743a', medkit: '#2f9e5b', battery: '#e0b23a'};

/** Everything we have, laid out on the floor and counted. items: can, water, dogfood, flashlight, candle, radio,
 * battery, medkit, map, rope, bat, backpack, keys, walkie; "can:3" shows a count. */
export const Supplies: React.FC<SceneProps> = ({p, f}) => {
	const items = list(p.items).slice(0, 9);
	const cols = [220, 540, 860];
	return (
		<Svg>
			{Array.from({length: 12}, (_, i) => (
				<rect key={i} x={0} y={i * 160} width={W} height={156} fill={i % 2 ? '#2c2119' : '#31251c'} />
			))}
			<circle cx={540} cy={960} r={900} fill="url(#warmGlow)" opacity={0.22} />
			{items.map((raw, i) => {
				const [name, count] = raw.split(':');
				const x = cols[i % 3];
				const y = 560 + Math.floor(i / 3) * 360;
				const s = clamp((f - 6 - i * 7) / 8);
				const color = ITEM_COLORS[name] ?? '#9aa3b5';
				return (
					<g key={i} transform={`translate(${x} ${y}) scale(${s})`}>
						<ellipse cx={0} cy={110} rx={120} ry={20} fill="#000" opacity={0.3} />
						<Item name={name} color={color} />
						{count ? (
							<text x={90} y={-80} fill="#f2e6c9" fontSize={64} fontFamily="Special Elite, monospace">
								x{count}
							</text>
						) : null}
					</g>
				);
			})}
			<rect width={W} height={H} fill="#03050c" opacity={0.25} />
		</Svg>
	);
};

const Item: React.FC<{name: string; color: string}> = ({name, color}) => {
	switch (name) {
		case 'can':
			return (
				<g>
					<rect x={-60} y={-80} width={120} height={180} rx={14} fill="#8b8f96" />
					<rect x={-60} y={-30} width={120} height={80} fill={color} />
					<ellipse cx={0} cy={-80} rx={60} ry={14} fill="#b0b4bb" />
				</g>
			);
		case 'water':
			return (
				<g>
					<rect x={-45} y={-90} width={90} height={200} rx={26} fill={color} opacity={0.75} />
					<rect x={-22} y={-130} width={44} height={44} rx={8} fill="#2a5ea0" />
				</g>
			);
		case 'dogfood':
			return (
				<g>
					<path d="M-90 -100 L90 -100 L110 110 L-110 110 Z" fill={color} />
					<circle cx={0} cy={10} r={44} fill="#f2e1c4" />
					<circle cx={0} cy={20} r={16} fill="#6b4a2a" />
				</g>
			);
		case 'flashlight':
			return (
				<g transform="rotate(-30)">
					<rect x={-110} y={-30} width={170} height={60} rx={14} fill="#30343c" />
					<path d="M60 -45 L120 -60 L120 60 L60 45 Z" fill="#454a54" />
					<rect x={116} y={-56} width={10} height={112} fill="#fff4c8" />
				</g>
			);
		case 'candle':
			return (
				<g>
					<rect x={-26} y={-60} width={52} height={160} fill="#efe7d4" />
					<ellipse cx={0} cy={-84} rx={12} ry={24} fill="#ffcf6b" />
				</g>
			);
		case 'radio':
			return (
				<g>
					<rect x={-110} y={-70} width={220} height={150} rx={22} fill="#4a3a2f" />
					<circle cx={-50} cy={5} r={44} fill="#2a211c" />
					<rect x={10} y={-40} width={80} height={40} rx={6} fill="#e0a540" />
				</g>
			);
		case 'battery':
			return (
				<g>
					{[-50, 0, 50].map((x) => (
						<g key={x}>
							<rect x={x - 20} y={-70} width={40} height={150} rx={8} fill="#2a2a2a" />
							<rect x={x - 20} y={-70} width={40} height={60} rx={8} fill={color} />
						</g>
					))}
				</g>
			);
		case 'medkit':
			return (
				<g>
					<rect x={-110} y={-80} width={220} height={170} rx={20} fill={color} />
					<rect x={-40} y={-130} width={80} height={56} rx={14} fill="none" stroke={color} strokeWidth={14} />
					<rect x={-14} y={-50} width={28} height={110} fill="#fff" />
					<rect x={-55} y={-9} width={110} height={28} fill="#fff" />
				</g>
			);
		case 'map':
			return (
				<g>
					<path d="M-110 -90 L-40 -110 L40 -90 L110 -110 L110 100 L40 120 L-40 100 L-110 120 Z" fill="#d9caa0" />
					<path d="M-80 60 Q-20 -40 60 10 T90 -70" stroke={C.red} strokeWidth={6} strokeDasharray="14 10" fill="none" />
					<path d="M78 -82 L98 -62 M98 -82 L78 -62" stroke={C.red} strokeWidth={8} />
				</g>
			);
		case 'rope':
			return (
				<g fill="none" stroke="#b08a52" strokeWidth={16}>
					<circle r={90} />
					<circle r={64} />
					<circle r={38} />
				</g>
			);
		case 'bat':
			return <path d="M-130 70 L-110 90 L100 -70 Q130 -100 110 -110 Q90 -120 70 -90 Z" fill="#a37a4a" />;
		case 'backpack':
			return (
				<g>
					<rect x={-100} y={-100} width={200} height={210} rx={50} fill="#3d5a4a" />
					<rect x={-70} y={10} width={140} height={80} rx={20} fill="#33503f" />
					<path d="M-50 -100 Q0 -160 50 -100" stroke="#2a4033" strokeWidth={16} fill="none" />
				</g>
			);
		case 'keys':
			return (
				<g stroke="#d6c08a" strokeWidth={14} fill="none">
					<circle cx={-40} cy={-30} r={36} />
					<path d="M-10 -10 L90 70 M60 46 L76 30 M80 62 L96 46" />
				</g>
			);
		case 'walkie':
			return (
				<g>
					<rect x={-55} y={-90} width={110} height={200} rx={20} fill="#2c3036" />
					<rect x={20} y={-150} width={16} height={70} fill="#2c3036" />
					<rect x={-35} y={-60} width={70} height={50} rx={6} fill="#7fd08a" opacity={0.7} />
				</g>
			);
		default:
			return <rect x={-80} y={-80} width={160} height={160} rx={24} fill={color} />;
	}
};

export const SCENES: Record<string, React.FC<SceneProps>> = {
	building: Building,
	window: WindowView,
	street: Street,
	rooftop: Rooftop,
	room: Room,
	door: Door,
	peephole: Peephole,
	hallway: Hallway,
	stairwell: Stairwell,
	kitchen: Kitchen,
	phone: Phone,
	radio: Radio,
	supplies: Supplies,
	tower: Tower,
	office: Office,
	elevator: Elevator,
	forest: Forest,
	cabin: Cabin,
	truck: Truck,
	lake: Lake,
	gas_station: GasStation,
	supermarket: Supermarket,
	hospital: Hospital,
	school: School,
	subway: Subway,
	skybridge: Skybridge,
	lobby: Lobby,
};

/** Where the camera can look in each scene: the first point is the wide shot's centre, the others are close-ups
 * (a face, a door, a dial...). Consecutive beats in one scene cut between them, so a scene never sits still. */
export const SHOTS: Record<string, [number, number][]> = {
	building: [[540, 900], [540, 700], [540, 1720]],
	window: [[540, 960], [320, 820], [760, 1200]],
	street: [[540, 1100], [330, 1480], [780, 1380]],
	rooftop: [[540, 1100], [320, 1100], [840, 1000]],
	room: [[560, 1200], [300, 1150], [640, 1640], [540, 600]],
	door: [[540, 1000], [540, 640], [790, 960], [540, 1700]],
	peephole: [[540, 900]],
	hallway: [[540, 860], [540, 720], [300, 1150]],
	stairwell: [[540, 960], [540, 940]],
	kitchen: [[700, 1100], [300, 1080], [880, 1050]],
	phone: [[540, 900], [540, 760]],
	radio: [[540, 980], [430, 1000], [770, 900]],
	supplies: [[540, 900], [380, 700], [700, 1100]],
	tower: [[540, 900], [540, 500], [540, 1760]],
	office: [[540, 1000], [300, 1300], [880, 1100]],
	elevator: [[540, 900], [540, 350], [540, 1000], [940, 950]],
	forest: [[540, 1250], [540, 1500], [300, 1380]],
	cabin: [[600, 1200], [270, 600], [830, 1300], [220, 1400]],
	truck: [[540, 900], [540, 1000], [700, 1450]],
	lake: [[540, 1100], [540, 1400], [760, 1420]],
	gas_station: [[540, 1100], [330, 1300], [880, 900]],
	supermarket: [[540, 960], [300, 1000], [780, 1000]],
	hospital: [[540, 960], [820, 1450], [540, 860]],
	school: [[540, 960], [260, 1000], [540, 1650]],
	subway: [[540, 960], [540, 860], [250, 1200]],
	skybridge: [[540, 960], [540, 760], [260, 640]],
	lobby: [[540, 960], [540, 860], [140, 900], [950, 900]],
};

/** Outdoor scenes without writing in them can be mirrored from part to part, which changes the whole composition. */
export const FLIPPABLE = new Set(['building', 'window', 'street', 'rooftop', 'forest', 'tower', 'hallway', 'lake', 'gas_station', 'supermarket', 'skybridge']);
