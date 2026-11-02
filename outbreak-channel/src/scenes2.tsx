import React from 'react';
import {C, FireGlow, H, Moon, Sitter, Skyline, Smoke, Stars, W, Walker, flicker, hash, lerp} from './art';
import type {Params} from './scenes';

// Scenes for the Floor 41 (Meridian Tower) and Pine Hollow (lake cabin) stories. Same conventions as scenes.tsx.
type SceneProps = {p: Params; f: number};

const num = (v: unknown, d: number) => (typeof v === 'number' ? v : d);
const str = (v: unknown, d: string) => (typeof v === 'string' ? v : d);

const Svg: React.FC<{children: React.ReactNode}> = ({children}) => (
	<svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: 'absolute', inset: 0}}>
		{children}
	</svg>
);

const Pine: React.FC<{x: number; y: number; h: number; color: string}> = ({x, y, h, color}) => (
	<path
		d={`M${x} ${y - h} L${x + h * 0.16} ${y - h * 0.7} L${x + h * 0.09} ${y - h * 0.7} L${x + h * 0.24} ${y - h * 0.42} L${x + h * 0.13} ${y - h * 0.42} L${x + h * 0.3} ${y - h * 0.12} L${x + h * 0.04} ${y - h * 0.12} L${x + h * 0.04} ${y} L${x - h * 0.04} ${y} L${x - h * 0.04} ${y - h * 0.12} L${x - h * 0.3} ${y - h * 0.12} L${x - h * 0.13} ${y - h * 0.42} L${x - h * 0.24} ${y - h * 0.42} L${x - h * 0.09} ${y - h * 0.7} L${x - h * 0.16} ${y - h * 0.7} Z`}
		fill={color}
	/>
);

// ---------------------------------------------------------------- Floor 41
/** Meridian Tower from the street: a glass skyscraper with one lit floor (41) near the top. */
export const Tower: React.FC<SceneProps> = ({p, f}) => {
	const zombies = num(p.zombies, 0);
	const top = 140;
	const litY = 470;
	return (
		<Svg>
			<rect width={W} height={H} fill="url(#nightSky)" />
			<Stars frame={f} n={60} maxY={600} seed={5} />
			{p.fire ? <FireGlow x={160} y={1300} r={420} frame={f} /> : null}
			<Smoke frame={f} xs={[120, 950]} base={1400} />
			<rect x={-40} y={420} width={300} height={H} fill="#121a30" />
			<rect x={830} y={600} width={300} height={H} fill="#10172b" />
			{Array.from({length: 30}, (_, i) => (
				<rect key={i} x={i % 2 ? 860 + hash(i) * 200 : hash(i) * 220} y={460 + hash(i + 9) * 1200} width={14} height={20} fill="#e8c27a" opacity={hash(i + 3) < 0.25 ? 0.5 : 0} />
			))}
			<path d={`M300 ${top} L780 ${top + 60} L780 ${H} L300 ${H} Z`} fill="#16223f" />
			{Array.from({length: 9}, (_, i) => (
				<line key={`v${i}`} x1={300 + i * 60} y1={top + i * 7.5} x2={300 + i * 60} y2={H} stroke="#0c1428" strokeWidth={4} />
			))}
			{Array.from({length: 52}, (_, i) => {
				const y = top + 70 + i * 34;
				return <line key={`h${i}`} x1={300} y1={y} x2={780} y2={y} stroke="#0c1428" strokeWidth={3} />;
			})}
			<path d={`M300 ${top + 300} L780 ${top - 100} L780 ${top + 200} L300 ${top + 600} Z`} fill="#8fb0ff" opacity={0.05} />
			<rect x={302} y={litY} width={476} height={30} fill={C.warm} opacity={0.85 * flicker(f, 41, 0.97)} />
			<rect x={240} y={litY - 60} width={600} height={150} fill="url(#warmGlow)" opacity={0.35} />
			<path d={`M540 ${top + 30} L540 ${top - 120}`} stroke="#0e1426" strokeWidth={8} />
			<circle cx={540} cy={top - 122} r={8} fill={C.red} opacity={Math.floor(f / 20) % 2 ? 1 : 0.2} />
			{p.heli ? (
				<g transform={`translate(${-200 + ((f * 5) % 1500)} ${top - 40})`}>
					<ellipse rx={50} ry={18} fill="#0b0d14" />
					<rect x={34} y={-5} width={70} height={8} fill="#0b0d14" />
					<rect x={-60} y={-26} width={120} height={4} fill="#0b0d14" />
					<path d="M0 10 L-160 700 L160 700 Z" fill="#fff7d6" opacity={0.07} />
				</g>
			) : null}
			<rect x={300} y={1640} width={480} height={280} fill="#0d1322" />
			<rect x={420} y={1680} width={240} height={240} fill="#9fb8e8" opacity={0.12 + 0.05 * flicker(f, 5)} />
			{Array.from({length: zombies}, (_, i) => (
				<Walker key={i} x={((hash(i + 3) * 1300 + f * (0.4 + hash(i) * 0.4)) % 1300) - 110} y={1900 - hash(i + 9) * 40} h={130} frame={f} seed={i} flip={i % 2 === 1} />
			))}
		</Svg>
	);
};

/** The open-plan office on floor 41: desks with glowing screens and the burning city behind the glass.
 * light: on, flicker or off. zombie: a shape behind the frosted glass of the meeting room. guest: dev at a desk. */
export const Office: React.FC<SceneProps> = ({p, f}) => {
	const light = str(p.light, 'off');
	const on = light === 'on' ? 1 : light === 'off' ? 0 : flicker(f, 11, 0.6);
	return (
		<Svg>
			<rect width={W} height={H} fill="#151a28" />
			<rect x={0} y={200} width={W} height={900} fill="url(#nightSky)" />
			<Skyline base={1100} seed={41} color="#101830" maxH={560} lit={0.08} />
			{p.fire !== false ? <FireGlow x={760} y={1000} r={300} frame={f} /> : null}
			<Smoke frame={f} xs={[760]} base={1000} />
			{Array.from({length: 7}, (_, i) => (
				<rect key={i} x={i * 180 - 10} y={200} width={20} height={900} fill="#0d111c" />
			))}
			<rect x={0} y={170} width={W} height={40} fill="#0d111c" />
			<rect x={0} y={1090} width={W} height={30} fill="#0d111c" />
			<rect x={0} y={0} width={W} height={170} fill="#1b2030" />
			{[200, 540, 880].map((x, i) => (
				<rect key={i} x={x - 120} y={50} width={240} height={40} rx={6} fill="#eef3ff" opacity={0.15 + 0.85 * on * flicker(f, i + 30, 0.9)} />
			))}
			<rect y={1120} width={W} height={800} fill="#1c1f2a" />
			{p.zombie ? (
				<g>
					<rect x={720} y={760} width={360} height={720} fill="#9fb0c8" opacity={0.18} />
					<g opacity={0.6} filter="url(#blur8)">
						<Walker x={880 + Math.sin(f / 40) * 40} y={1460} h={560} frame={f} seed={4} color="#05070c" />
					</g>
					<rect x={720} y={760} width={360} height={720} fill="none" stroke="#0d111c" strokeWidth={10} />
				</g>
			) : null}
			{[1260, 1560].map((y, row) =>
				[120, 470].map((x, k) => (
					<g key={`${row}-${k}`}>
						<rect x={x} y={y} width={300} height={24} fill="#3a3f4d" />
						<rect x={x + 10} y={y + 24} width={14} height={140} fill="#2a2e38" />
						<rect x={x + 276} y={y + 24} width={14} height={140} fill="#2a2e38" />
						<rect x={x + 90} y={y - 120} width={130} height={90} rx={6} fill="#0a0d16" />
						<rect x={x + 96} y={y - 114} width={118} height={78} fill="#6fa8ff" opacity={0.35 + 0.25 * flicker(f, row * 2 + k + 50, 0.8)} />
						<rect x={x + 148} y={y - 30} width={14} height={30} fill="#0a0d16" />
						<circle cx={x + 155} cy={y - 75} r={120} fill="url(#coolGlow)" opacity={0.4} />
					</g>
				)),
			)}
			{p.guest ? <Sitter x={300} y={1440} s={0.95} frame={f} who={str(p.guest, 'dev')} /> : null}
			<rect width={W} height={H} fill="#03050c" opacity={0.5 - 0.35 * on} />
		</Svg>
	);
};

/** Inside a lift. doors: closed, open or gap (hands reaching through). floor: the number on the display.
 * power: false gives only the red emergency light. */
export const Elevator: React.FC<SceneProps> = ({p, f}) => {
	const doors = str(p.doors, 'closed');
	const power = p.power !== false;
	const open = doors === 'open' ? 260 : doors === 'gap' ? 40 + Math.sin(f / 6) * 6 : 0;
	return (
		<Svg>
			<rect width={W} height={H} fill="#4a515c" />
			{Array.from({length: 24}, (_, i) => (
				<rect key={i} x={i * 46} y={0} width={2} height={H} fill="#5d6570" opacity={0.6} />
			))}
			<rect y={1700} width={W} height={220} fill="#2a2d33" />
			<rect x={0} y={1180} width={W} height={18} fill="#8a919b" />
			<rect x={240} y={420} width={600} height={1300} fill="#05060a" />
			<rect x={540 - open - 290} y={440} width={290} height={1260} fill="#7c838d" />
			<rect x={540 + open} y={440} width={290} height={1260} fill="#747b85" />
			{doors === 'gap'
				? [0, 1, 2].map((i) => (
						<path
							key={i}
							d={`M${540 - open - 6} ${760 + i * 210} l${70 + Math.sin(f / 5 + i) * 14} -14 l26 -6 l4 12 l-24 8 l28 2 l2 12 l-30 0 l24 10 l-4 12 l-30 -8 l-60 10 Z`}
							fill="#6d7560"
							stroke="#2c3028"
							strokeWidth={4}
						/>
					))
				: null}
			<rect x={420} y={300} width={240} height={90} rx={10} fill="#0b0b0d" />
			<text x={540} y={372} textAnchor="middle" fill="#ff4a3a" fontSize={72} fontFamily="monospace" opacity={power ? 1 : 0.5}>
				{num(p.floor, 41)}
			</text>
			<rect x={890} y={760} width={110} height={400} rx={12} fill="#5c636e" />
			{Array.from({length: 10}, (_, i) => (
				<circle key={i} cx={920 + (i % 2) * 50} cy={800 + Math.floor(i / 2) * 70} r={18} fill={i === 3 ? '#ffb347' : '#3d434c'} opacity={power ? 1 : 0.4} />
			))}
			{power ? <rect width={W} height={H} fill="#fff6e0" opacity={0.06 * flicker(f, 21, 0.9)} /> : <rect width={W} height={H} fill="#c0201a" opacity={0.35 + 0.1 * Math.sin(f / 8)} style={{mixBlendMode: 'multiply'}} />}
			<rect width={W} height={H} fill="#03050c" opacity={power ? 0.25 : 0.45} />
		</Svg>
	);
};

// ---------------------------------------------------------------- Pine Hollow
/** Night woods around the lake. zombies: walkers between the trees. cabin: the cabin's lit window far away. */
export const Forest: React.FC<SceneProps> = ({p, f}) => {
	const zombies = num(p.zombies, 0);
	return (
		<Svg>
			<rect width={W} height={H} fill="url(#nightSky)" />
			<Stars frame={f} n={80} maxY={900} seed={12} />
			<Moon x={760} y={330} r={66} />
			{p.fire ? <FireGlow x={300} y={1150} r={380} frame={f} /> : null}
			{Array.from({length: 14}, (_, i) => (
				<Pine key={`a${i}`} x={i * 85 - 20 + hash(i) * 40} y={1250} h={420 + hash(i + 3) * 260} color="#121a2a" />
			))}
			{p.cabin ? (
				<g>
					<path d="M470 1170 L540 1110 L610 1170 L610 1240 L470 1240 Z" fill="#0d1018" />
					<rect x={512} y={1180} width={30} height={26} fill={C.warm} opacity={0.9} />
					<circle cx={527} cy={1193} r={90} fill="url(#warmGlow)" opacity={0.6} />
				</g>
			) : null}
			{Array.from({length: 9}, (_, i) => (
				<Pine key={`b${i}`} x={i * 135 - 40 + hash(i + 20) * 60} y={1500} h={760 + hash(i + 8) * 300} color="#0b111c" />
			))}
			<rect y={1240} width={W} height={680} fill="#0a0e16" />
			<path d={`M420 1920 Q560 1600 520 1260 L560 1260 Q640 1600 700 1920 Z`} fill="#1a1f2a" />
			{Array.from({length: zombies}, (_, i) => {
				const depth = 0.3 + hash(i + 14) * 0.7;
				const y = lerp(1300, 1880, depth);
				const dir = hash(i + 2) < 0.5 ? 1 : -1;
				const x = ((hash(i + 5) * 1400 + f * dir * (0.3 + depth * 0.6)) % 1400 + 1400) % 1400 - 160;
				return <Walker key={i} x={x} y={y} h={lerp(160, 520, depth)} frame={f} seed={i + 3} flip={dir < 0} eyes={depth > 0.6} color={depth < 0.5 ? '#1d2436' : C.ink} />;
			})}
			<Pine x={60} y={1980} h={1500} color="#05070c" />
			<Pine x={1040} y={2000} h={1400} color="#05070c" />
			<rect x={0} y={1180} width={W} height={260} fill="#55617d" opacity={0.15} filter="url(#blur24)" />
		</Svg>
	);
};

/** The ranger cabin: log walls, a stone fireplace, a window on the woods. light: fire, lantern or off. guest: ava. */
export const Cabin: React.FC<SceneProps> = ({p, f}) => {
	const light = str(p.light, 'fire');
	const flame = 0.85 + 0.15 * Math.sin(f / 2.3) * Math.sin(f / 3.7);
	return (
		<Svg>
			{Array.from({length: 16}, (_, i) => (
				<rect key={i} x={0} y={i * 90} width={W} height={88} rx={40} fill={i % 2 ? '#4a301f' : '#53361f'} />
			))}
			<rect y={1430} width={W} height={490} fill="#2b1d14" />
			{Array.from({length: 6}, (_, i) => (
				<rect key={`f${i}`} x={0} y={1440 + i * 82} width={W} height={4} fill="#22170f" />
			))}
			<g>
				<rect x={90} y={360} width={360} height={460} fill={p.zombie ? '#34446e' : 'url(#nightSky)'} />
				<Moon x={330} y={460} r={30} />
				{[0, 1, 2, 3].map((i) => (
					<Pine key={i} x={110 + i * 100} y={820} h={260 + hash(i) * 120} color="#0a0e18" />
				))}
				{p.zombie ? <Walker x={230 + Math.sin(f / 50) * 30} y={860} h={330} frame={f} seed={6} eyes /> : null}
				<rect x={90} y={360} width={360} height={460} fill="none" stroke="#2a1a10" strokeWidth={24} />
				<rect x={260} y={360} width={20} height={460} fill="#2a1a10" />
				<rect x={90} y={580} width={360} height={18} fill="#2a1a10" />
			</g>
			<g>
				<rect x={640} y={700} width={380} height={760} fill="#5a5a5e" />
				{Array.from({length: 18}, (_, i) => (
					<rect key={i} x={640 + (i % 3) * 126 + (Math.floor(i / 3) % 2) * 60} y={700 + Math.floor(i / 3) * 126} width={120} height={120} rx={14} fill="#66666b" stroke="#4a4a4f" strokeWidth={6} />
				))}
				<rect x={700} y={1110} width={260} height={350} fill="#120c09" />
				{light === 'fire' ? (
					<g>
						<path d={`M740 1450 Q760 ${1300 - 40 * flame} 800 ${1240 - 30 * flame} Q820 ${1330 + 10 * flame} 850 ${1200 - 50 * flame} Q880 1320 920 1450 Z`} fill="#ff8a2a" />
						<path d={`M780 1450 Q800 ${1350 - 20 * flame} 830 ${1300 - 30 * flame} Q860 1370 880 1450 Z`} fill="#ffd36a" />
						<circle cx={830} cy={1330} r={700} fill="url(#warmGlow)" opacity={0.5 * flame} />
					</g>
				) : null}
				<rect x={620} y={1080} width={420} height={40} fill="#3b2a1d" />
			</g>
			<g>
				<rect x={240} y={1300} width={360} height={30} fill="#3b2617" />
				<rect x={260} y={1330} width={20} height={200} fill="#2b1b10" />
				<rect x={560} y={1330} width={20} height={200} fill="#2b1b10" />
				{light === 'lantern' ? (
					<g>
						<rect x={400} y={1220} width={50} height={80} rx={10} fill="#3a3a3a" />
						<rect x={410} y={1232} width={30} height={52} fill="#ffd27a" opacity={0.85 * flame} />
						<circle cx={425} cy={1258} r={600} fill="url(#warmGlow)" opacity={0.45 * flame} />
					</g>
				) : null}
			</g>
			{p.guest ? <Sitter x={200} y={1560} s={1.05} frame={f} who={str(p.guest, 'ava')} /> : null}
			<path d={`M0 0 H${W} V${H} H0 Z M90 360 V820 H450 V360 Z`} fillRule="evenodd" fill="#03050c" opacity={light === 'off' ? 0.65 : 0.25} />
			<rect x={90} y={360} width={360} height={460} fill="#03050c" opacity={light === 'off' ? 0.2 : 0.1} />
		</Svg>
	);
};

/** Inside Noah's old pickup at night: the road in the headlights. zombies: walkers in the lights. wipers: on. */
export const Truck: React.FC<SceneProps> = ({p, f}) => {
	const zombies = num(p.zombies, 0);
	const lights = p.lights !== false;
	const wipe = p.wipers ? Math.abs(((f % 40) / 20) - 1) : 0;
	const hz = 760;
	return (
		<Svg>
			<rect width={W} height={1300} fill="url(#nightSky)" />
			{[0, 1, 2, 3, 4].map((i) => (
				<Pine key={`l${i}`} x={60 + i * 70} y={hz + 30 + i * 40} h={420 - i * 40} color="#0b101b" />
			))}
			{[0, 1, 2, 3, 4].map((i) => (
				<Pine key={`r${i}`} x={1020 - i * 70} y={hz + 30 + i * 40} h={420 - i * 40} color="#0b101b" />
			))}
			<path d={`M500 ${hz} L580 ${hz} L1100 1300 L-20 1300 Z`} fill="#16181e" />
			{[0, 1, 2, 3].map((k) => {
				const t = ((k / 4 + f * 0.02) % 1) ** 2;
				return <rect key={k} x={536 - lerp(2, 14, t)} y={lerp(hz + 10, 1290, t)} width={lerp(4, 28, t)} height={lerp(8, 70, t)} fill="#d9d4bc" opacity={0.5} />;
			})}
			{lights ? <path d={`M140 1300 L470 ${hz + 60} L610 ${hz + 60} L940 1300 Z`} fill="#fff4cc" opacity={0.13} /> : null}
			{Array.from({length: zombies}, (_, i) => {
				const depth = ((hash(i + 7) + f * 0.004) % 1) * 0.8 + 0.1;
				const y = lerp(hz + 30, 1260, depth);
				const x = 540 + (hash(i + 2) - 0.5) * lerp(200, 900, depth);
				return <Walker key={i} x={x} y={y} h={lerp(90, 520, depth)} frame={f} seed={i + 9} flip={hash(i) < 0.5} eyes color={lights ? '#2a2f3a' : C.ink} />;
			})}
			<path d={`M0 0 L${W} 0 L${W} 200 Q540 120 0 200 Z`} fill="#0a0b0f" />
			<path d={`M0 0 L120 0 L60 1300 L0 1300 Z`} fill="#0a0b0f" />
			<path d={`M${W} 0 L${W - 120} 0 L${W - 60} 1300 L${W} 1300 Z`} fill="#0a0b0f" />
			{p.wipers ? <line x1={300} y1={1290} x2={300 + Math.cos(Math.PI * (1 - wipe * 0.8)) * 520} y2={1290 - Math.sin(Math.PI * (1 - wipe * 0.8)) * 520} stroke="#05060a" strokeWidth={14} strokeLinecap="round" /> : null}
			<path d={`M0 1300 Q540 1180 ${W} 1300 L${W} ${H} L0 ${H} Z`} fill="#121318" />
			{[380, 700].map((x, i) => (
				<g key={i}>
					<circle cx={x} cy={1450} r={90} fill="#07080b" stroke="#2a2c33" strokeWidth={6} />
					<circle cx={x} cy={1450} r={78} fill="url(#warmGlow)" opacity={0.25} />
					<line x1={x} y1={1450} x2={x + Math.cos(-2.4 + i * 0.9 + Math.sin(f / 30) * 0.05) * 64} y2={1450 + Math.sin(-2.4 + i * 0.9) * 64} stroke="#ff8a3a" strokeWidth={6} />
				</g>
			))}
			<rect x={850} y={1400} width={170} height={70} rx={8} fill="#0b0d12" />
			<rect x={862} y={1412} width={146} height={46} fill="#7fd08a" opacity={0.35} />
			<path d="M140 1920 Q140 1640 540 1600 Q940 1640 940 1920" stroke="#050608" strokeWidth={60} fill="none" />
			<rect width={W} height={H} fill="#03050c" opacity={0.2} />
		</Svg>
	);
};
