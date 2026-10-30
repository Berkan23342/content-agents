import React, {useId} from 'react';

export const mix = (hex: string, target: string, amount: number) => {
	const p = (h: string) => {
		const full = h.length === 4 ? '#' + [...h.slice(1)].map((c) => c + c).join('') : h;
		return [1, 3, 5].map((i) => parseInt(full.slice(i, i + 2), 16));
	};
	const a = p(hex);
	const b = p(target);
	const c = a.map((v, i) => Math.round(v + (b[i] - v) * amount));
	return `rgb(${c[0]},${c[1]},${c[2]})`;
};

const useSafeId = () => useId().replace(/:/g, '');

/** Kawaii face: eyes, blush and smile. Drawn around (0,0). */
export const Face: React.FC<{blink?: number; scale?: number; x?: number; y?: number; open?: boolean}> = ({
	blink = 1,
	scale = 1,
	x = 0,
	y = 0,
	open = false,
}) => (
	<g transform={`translate(${x} ${y}) scale(${scale})`}>
		{[-25, 25].map((ex) => (
			<g key={ex} transform={`translate(${ex} 0) scale(1 ${blink})`}>
				<ellipse rx={9} ry={12} fill="#2b2b3a" />
				<circle cx={3} cy={-5} r={3.6} fill="#fff" />
			</g>
		))}
		<ellipse cx={-40} cy={20} rx={11} ry={7} fill="#ff7a9c" opacity={0.45} />
		<ellipse cx={40} cy={20} rx={11} ry={7} fill="#ff7a9c" opacity={0.45} />
		{open ? (
			<path d="M-14 18 Q0 40 14 18 Z" fill="#c2334d" stroke="#2b2b3a" strokeWidth={4} strokeLinejoin="round" />
		) : (
			<path d="M-14 19 Q0 33 14 19" fill="none" stroke="#2b2b3a" strokeWidth={5} strokeLinecap="round" />
		)}
	</g>
);

export const Balloon: React.FC<{color: string; width: number; blink?: number; sway?: number}> = ({
	color,
	width,
	blink = 1,
	sway = 0,
}) => {
	const id = useSafeId();
	return (
		<svg width={width} height={width * 1.6} viewBox="0 0 200 320" style={{overflow: 'visible'}}>
			<defs>
				<radialGradient id={`g${id}`} cx="35%" cy="30%" r="75%">
					<stop offset="0%" stopColor={mix(color, '#ffffff', 0.45)} />
					<stop offset="55%" stopColor={color} />
					<stop offset="100%" stopColor={mix(color, '#000000', 0.25)} />
				</radialGradient>
			</defs>
			<path
				d={`M100 205 C ${90 + sway} 235, ${115 - sway} 260, ${100 + sway * 1.5} 320`}
				stroke="#ffffff"
				strokeWidth={3}
				fill="none"
				opacity={0.9}
			/>
			<path d="M100 192 L88 210 L112 210 Z" fill={mix(color, '#000000', 0.2)} />
			<ellipse cx={100} cy={100} rx={82} ry={97} fill={`url(#g${id})`} />
			<ellipse cx={62} cy={52} rx={16} ry={26} fill="#fff" opacity={0.45} transform="rotate(-30 62 52)" />
			<Face x={100} y={105} blink={blink} />
		</svg>
	);
};

type IconProps = {color: string; blink: number};

const Shine: React.FC<{x: number; y: number; rx?: number; ry?: number}> = ({x, y, rx = 10, ry = 16}) => (
	<ellipse cx={x} cy={y} rx={rx} ry={ry} fill="#fff" opacity={0.4} transform={`rotate(-30 ${x} ${y})`} />
);

const starPath = (cx: number, cy: number, outer: number, inner: number) =>
	Array.from({length: 10}, (_, i) => {
		const r = i % 2 === 0 ? outer : inner;
		const a = (Math.PI / 5) * i - Math.PI / 2;
		return `${i === 0 ? 'M' : 'L'}${cx + r * Math.cos(a)} ${cy + r * Math.sin(a)}`;
	}).join(' ') + 'Z';

export const ICONS: Record<string, React.FC<IconProps>> = {
	apple: ({color, blink}) => (
		<>
			<rect x={95} y={25} width={10} height={35} rx={5} fill="#7a4a24" />
			<ellipse cx={128} cy={38} rx={22} ry={11} fill="#3cc75a" transform="rotate(-25 128 38)" />
			<path
				d="M100 60 C 60 30, 15 60, 25 115 C 35 170, 75 185, 100 172 C 125 185, 165 170, 175 115 C 185 60, 140 30, 100 60 Z"
				fill={color}
			/>
			<Shine x={60} y={80} />
			<Face x={100} y={115} scale={0.8} blink={blink} />
		</>
	),
	heart: ({color, blink}) => (
		<>
			<path
				d="M100 178 C 40 132, 8 98, 28 60 C 48 24, 90 34, 100 64 C 110 34, 152 24, 172 60 C 192 98, 160 132, 100 178 Z"
				fill={color}
			/>
			<Shine x={55} y={65} />
			<Face x={100} y={100} scale={0.75} blink={blink} />
		</>
	),
	carrot: ({color, blink}) => (
		<>
			{[-30, 0, 30].map((r) => (
				<ellipse key={r} cx={100} cy={38} rx={10} ry={28} fill="#3cc75a" transform={`rotate(${r} 100 62)`} />
			))}
			<path d="M58 62 Q100 50 142 62 Q130 130 104 188 Q100 194 96 188 Q70 130 58 62 Z" fill={color} />
			{[95, 125, 150].map((y) => (
				<path key={y} d={`M${76 + (y - 95) / 4} ${y} l14 3`} stroke={mix(color, '#000', 0.25)} strokeWidth={4} strokeLinecap="round" />
			))}
			<Face x={100} y={95} scale={0.6} blink={blink} />
		</>
	),
	pumpkin: ({color, blink}) => (
		<>
			<rect x={92} y={30} width={16} height={34} rx={6} fill="#6b4a1f" />
			<ellipse cx={62} cy={118} rx={48} ry={62} fill={mix(color, '#000', 0.12)} />
			<ellipse cx={138} cy={118} rx={48} ry={62} fill={mix(color, '#000', 0.12)} />
			<ellipse cx={100} cy={118} rx={50} ry={66} fill={color} />
			<Face x={100} y={122} scale={0.7} blink={blink} />
		</>
	),
	sun: ({color, blink}) => (
		<>
			{Array.from({length: 12}, (_, i) => (
				<rect key={i} x={93} y={8} width={14} height={34} rx={7} fill={color} transform={`rotate(${i * 30} 100 100)`} />
			))}
			<circle cx={100} cy={100} r={58} fill={color} stroke={mix(color, '#ff8a00', 0.4)} strokeWidth={5} />
			<Face x={100} y={100} scale={0.8} blink={blink} />
		</>
	),
	star: ({color, blink}) => (
		<>
			<path d={starPath(100, 108, 88, 40)} fill={color} stroke={color} strokeWidth={16} strokeLinejoin="round" />
			<Face x={100} y={112} scale={0.62} blink={blink} />
		</>
	),
	leaf: ({color}) => (
		<>
			<path d="M35 165 C 35 85, 95 32, 172 32 C 168 112, 118 168, 35 165 Z" fill={color} />
			<path d="M35 165 Q 100 105 165 40" stroke={mix(color, '#000', 0.25)} strokeWidth={6} fill="none" strokeLinecap="round" />
			{[70, 100, 125].map((p) => (
				<path key={p} d={`M${p} ${200 - p - 5} l -6 -30 M${p} ${200 - p - 5} l 30 6`} stroke={mix(color, '#000', 0.25)} strokeWidth={4} strokeLinecap="round" />
			))}
		</>
	),
	frog: ({color, blink}) => (
		<>
			{[60, 140].map((x) => (
				<g key={x}>
					<circle cx={x} cy={68} r={30} fill={color} />
					<circle cx={x} cy={66} r={19} fill="#fff" />
					<ellipse cx={x} cy={68} rx={9} ry={10 * blink} fill="#2b2b3a" />
				</g>
			))}
			<ellipse cx={100} cy={128} rx={82} ry={56} fill={color} />
			<ellipse cx={55} cy={140} rx={12} ry={7} fill="#ff7a9c" opacity={0.5} />
			<ellipse cx={145} cy={140} rx={12} ry={7} fill="#ff7a9c" opacity={0.5} />
			<path d="M62 132 Q100 165 138 132" stroke="#2b2b3a" strokeWidth={6} fill="none" strokeLinecap="round" />
		</>
	),
	fish: ({color, blink}) => (
		<>
			<path d="M140 100 L192 62 Q182 100 192 138 Z" fill={mix(color, '#000', 0.12)} />
			<ellipse cx={88} cy={100} rx={70} ry={50} fill={color} />
			<path d="M80 52 Q100 25 120 58 Z" fill={mix(color, '#000', 0.12)} />
			<Shine x={55} y={78} />
			<Face x={70} y={98} scale={0.62} blink={blink} />
			<circle cx={20} cy={50} r={8} fill="none" stroke="#fff" strokeWidth={3} />
			<circle cx={8} cy={22} r={5} fill="none" stroke="#fff" strokeWidth={3} />
		</>
	),
	drop: ({color, blink}) => (
		<>
			<path d="M100 18 C 100 18, 40 96, 40 130 A 60 60 0 0 0 160 130 C 160 96, 100 18, 100 18 Z" fill={color} />
			<Shine x={70} y={110} />
			<Face x={100} y={140} scale={0.62} blink={blink} />
		</>
	),
	grapes: ({color}) => (
		<>
			<path d="M100 40 Q108 20 120 14" stroke="#6b4a1f" strokeWidth={7} fill="none" strokeLinecap="round" />
			<ellipse cx={130} cy={36} rx={24} ry={12} fill="#3cc75a" transform="rotate(-20 130 36)" />
			{[
				[70, 62], [100, 58], [130, 62],
				[55, 95], [85, 92], [115, 92], [145, 95],
				[70, 125], [100, 124], [130, 125],
				[85, 155], [115, 155], [100, 182],
			].map(([x, y], i) => (
				<g key={i}>
					<circle cx={x} cy={y} r={22} fill={color} stroke={mix(color, '#000', 0.18)} strokeWidth={3} />
					<circle cx={x - 7} cy={y - 7} r={5} fill="#fff" opacity={0.45} />
				</g>
			))}
		</>
	),
	flower: ({color, blink}) => (
		<>
			<path d="M100 130 Q96 170 100 198" stroke="#3cc75a" strokeWidth={8} fill="none" />
			{Array.from({length: 6}, (_, i) => (
				<ellipse key={i} cx={100} cy={52} rx={26} ry={38} fill={color} transform={`rotate(${i * 60} 100 92)`} />
			))}
			<circle cx={100} cy={92} r={34} fill="#ffd23f" />
			<Face x={100} y={92} scale={0.45} blink={blink} />
		</>
	),
	pig: ({color, blink}) => (
		<>
			<path d="M40 60 L52 12 L88 42 Z" fill={mix(color, '#000', 0.1)} strokeLinejoin="round" />
			<path d="M160 60 L148 12 L112 42 Z" fill={mix(color, '#000', 0.1)} strokeLinejoin="round" />
			<circle cx={100} cy={105} r={78} fill={color} />
			<g transform={`translate(0 0)`}>
				{[-28, 28].map((ex) => (
					<g key={ex} transform={`translate(${100 + ex} 82) scale(1 ${blink})`}>
						<ellipse rx={9} ry={12} fill="#2b2b3a" />
						<circle cx={3} cy={-5} r={3.6} fill="#fff" />
					</g>
				))}
			</g>
			<ellipse cx={100} cy={125} rx={34} ry={24} fill={mix(color, '#c2334d', 0.25)} />
			<ellipse cx={88} cy={125} rx={6} ry={9} fill="#7a2a40" />
			<ellipse cx={112} cy={125} rx={6} ry={9} fill="#7a2a40" />
			<ellipse cx={50} cy={120} rx={11} ry={7} fill="#ff4f88" opacity={0.4} />
			<ellipse cx={150} cy={120} rx={11} ry={7} fill="#ff4f88" opacity={0.4} />
		</>
	),
	icecream: ({color, blink}) => (
		<>
			<path d="M58 100 L142 100 L104 192 Q100 198 96 192 Z" fill="#e8b46a" />
			{[0, 1, 2].map((i) => (
				<path key={i} d={`M${70 + i * 22} 100 L${108 + i * 8} 175`} stroke="#c98d3f" strokeWidth={4} />
			))}
			<circle cx={100} cy={72} r={52} fill={color} />
			<path d="M50 88 Q60 112 72 92 Q84 116 98 94 Q112 116 126 92 Q138 112 150 88 Z" fill={color} />
			<circle cx={100} cy={20} r={13} fill="#ff3b3b" />
			<Shine x={74} y={52} rx={8} ry={13} />
			<Face x={100} y={78} scale={0.6} blink={blink} />
		</>
	),
};

export const Icon: React.FC<{name: string; color: string; size: number; blink: number}> = ({name, color, size, blink}) => {
	const Comp = ICONS[name];
	return (
		<svg width={size} height={size} viewBox="0 0 200 200" style={{overflow: 'visible'}}>
			<Comp color={color} blink={blink} />
		</svg>
	);
};
