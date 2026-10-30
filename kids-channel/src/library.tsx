import React from 'react';
import {Face, ICONS, mix} from './shapes';

type P = {color: string; blink: number; headOnly?: boolean};

const Shine: React.FC<{x: number; y: number; rx?: number; ry?: number}> = ({x, y, rx = 10, ry = 16}) => (
	<ellipse cx={x} cy={y} rx={rx} ry={ry} fill="#fff" opacity={0.4} transform={`rotate(-30 ${x} ${y})`} />
);

const Eyes: React.FC<{y: number; dx?: number; blink: number; r?: number; cx?: number}> = ({y, dx = 26, blink, r = 1, cx = 100}) => (
	<>
		{[-dx, dx].map((ex) => (
			<g key={ex} transform={`translate(${cx + ex} ${y}) scale(${r} ${r * blink})`}>
				<ellipse rx={9} ry={12} fill="#2b2b3a" />
				<circle cx={3} cy={-5} r={3.6} fill="#fff" />
			</g>
		))}
	</>
);

const Cheeks: React.FC<{y: number; dx?: number}> = ({y, dx = 48}) => (
	<>
		<ellipse cx={100 - dx} cy={y} rx={12} ry={7} fill="#ff6f91" opacity={0.4} />
		<ellipse cx={100 + dx} cy={y} rx={12} ry={7} fill="#ff6f91" opacity={0.4} />
	</>
);

const Smile: React.FC<{y: number; w?: number}> = ({y, w = 14}) => (
	<path d={`M${100 - w} ${y} Q100 ${y + w} ${100 + w} ${y}`} fill="none" stroke="#2b2b3a" strokeWidth={5} strokeLinecap="round" />
);

const starPath = (cx: number, cy: number, outer: number, inner: number, n = 5) =>
	Array.from({length: n * 2}, (_, i) => {
		const r = i % 2 === 0 ? outer : inner;
		const a = (Math.PI / n) * i - Math.PI / 2;
		return `${i === 0 ? 'M' : 'L'}${cx + r * Math.cos(a)} ${cy + r * Math.sin(a)}`;
	}).join(' ') + 'Z';

// ---------------------------------------------------------------- animals (fixed palettes)
const ANIMALS: Record<string, React.FC<P>> = {
	cat: ({blink}) => (
		<>
			<path d="M35 80 L45 15 L90 50 Z" fill="#f6a44c" strokeLinejoin="round" />
			<path d="M165 80 L155 15 L110 50 Z" fill="#f6a44c" strokeLinejoin="round" />
			<path d="M48 62 L52 32 L76 52 Z" fill="#ffb3c6" />
			<path d="M152 62 L148 32 L124 52 Z" fill="#ffb3c6" />
			<ellipse cx={100} cy={112} rx={78} ry={70} fill="#f6a44c" />
			<path d="M100 48 L92 70 M100 48 L108 70 M100 48 L100 72" stroke="#d9822b" strokeWidth={6} strokeLinecap="round" />
			<Eyes y={105} blink={blink} />
			<path d="M92 128 L108 128 L100 137 Z" fill="#ff7a9c" />
			<path d="M100 137 Q92 148 84 140 M100 137 Q108 148 116 140" fill="none" stroke="#2b2b3a" strokeWidth={4} strokeLinecap="round" />
			{[-1, 1].map((s) => (
				<g key={s} stroke="#7a5230" strokeWidth={3} strokeLinecap="round">
					<path d={`M${100 + s * 40} 130 l${s * 45} -8`} />
					<path d={`M${100 + s * 40} 138 l${s * 45} 6`} />
				</g>
			))}
			<Cheeks y={128} dx={55} />
		</>
	),
	dog: ({blink}) => (
		<>
			<ellipse cx={100} cy={108} rx={72} ry={68} fill="#d9a066" />
			<ellipse cx={38} cy={100} rx={24} ry={52} fill="#8a5a33" transform="rotate(20 38 100)" />
			<ellipse cx={162} cy={100} rx={24} ry={52} fill="#8a5a33" transform="rotate(-20 162 100)" />
			<ellipse cx={130} cy={78} rx={22} ry={18} fill="#b07a45" />
			<ellipse cx={100} cy={140} rx={40} ry={30} fill="#f3d8b5" />
			<Eyes y={98} blink={blink} />
			<ellipse cx={100} cy={127} rx={13} ry={9} fill="#2b2b3a" />
			<path d="M100 136 L100 146 M100 146 Q90 156 82 148 M100 146 Q110 156 118 148" fill="none" stroke="#2b2b3a" strokeWidth={4} strokeLinecap="round" />
			<path d="M94 152 Q100 172 106 152 Z" fill="#ff7a9c" />
		</>
	),
	cow: ({blink}) => (
		<>
			<path d="M50 50 Q38 22 58 18 Q58 38 66 46 Z" fill="#f2e2c4" />
			<path d="M150 50 Q162 22 142 18 Q142 38 134 46 Z" fill="#f2e2c4" />
			<ellipse cx={30} cy={78} rx={24} ry={13} fill="#fff" stroke="#e8e8e8" strokeWidth={2} transform="rotate(-20 30 78)" />
			<ellipse cx={170} cy={78} rx={24} ry={13} fill="#fff" stroke="#e8e8e8" strokeWidth={2} transform="rotate(20 170 78)" />
			<ellipse cx={100} cy={100} rx={68} ry={74} fill="#fff" />
			<path d="M60 50 Q80 40 84 70 Q70 86 52 72 Z" fill="#2b2b3a" />
			<path d="M140 90 Q160 84 164 108 Q150 118 136 104 Z" fill="#2b2b3a" />
			<Eyes y={92} blink={blink} />
			<ellipse cx={100} cy={142} rx={50} ry={32} fill="#ffb3c6" />
			<ellipse cx={84} cy={140} rx={7} ry={10} fill="#d9667f" />
			<ellipse cx={116} cy={140} rx={7} ry={10} fill="#d9667f" />
		</>
	),
	sheep: ({blink}) => (
		<>
			{Array.from({length: 12}, (_, i) => {
				const a = (i / 12) * Math.PI * 2;
				return <circle key={i} cx={100 + Math.cos(a) * 66} cy={100 + Math.sin(a) * 62} r={30} fill="#fff" stroke="#ececec" strokeWidth={2} />;
			})}
			<ellipse cx={42} cy={100} rx={22} ry={12} fill="#5b5b6b" transform="rotate(-25 42 100)" />
			<ellipse cx={158} cy={100} rx={22} ry={12} fill="#5b5b6b" transform="rotate(25 158 100)" />
			<ellipse cx={100} cy={112} rx={48} ry={56} fill="#6b6b7b" />
			{[80, 100, 120].map((x) => (
				<circle key={x} cx={x} cy={58} r={18} fill="#fff" />
			))}
			<g transform="translate(0 0)">
				{[-20, 20].map((ex) => (
					<g key={ex} transform={`translate(${100 + ex} 108) scale(1 ${blink})`}>
						<ellipse rx={9} ry={11} fill="#fff" />
						<ellipse cy={1} rx={5} ry={7} fill="#2b2b3a" />
					</g>
				))}
			</g>
			<path d="M88 140 Q100 152 112 140" fill="none" stroke="#fff" strokeWidth={4} strokeLinecap="round" />
		</>
	),
	duck: ({blink}) => (
		<>
			<path d="M96 30 Q100 10 110 22 Q104 28 102 36 Z" fill="#ffd23f" />
			<circle cx={100} cy={100} r={74} fill="#ffd23f" />
			<Eyes y={86} blink={blink} dx={30} />
			<ellipse cx={100} cy={128} rx={42} ry={16} fill="#ff8a1f" />
			<ellipse cx={100} cy={140} rx={34} ry={12} fill="#e57412" />
			<Cheeks y={118} dx={58} />
		</>
	),
	lion: ({blink}) => (
		<>
			{Array.from({length: 14}, (_, i) => {
				const a = (i / 14) * Math.PI * 2;
				return <circle key={i} cx={100 + Math.cos(a) * 70} cy={104 + Math.sin(a) * 70} r={30} fill={i % 2 ? '#d9822b' : '#e8962f'} />;
			})}
			<circle cx={58} cy={58} r={16} fill="#f6c453" />
			<circle cx={142} cy={58} r={16} fill="#f6c453" />
			<circle cx={100} cy={106} r={66} fill="#f6c453" />
			<Eyes y={96} blink={blink} />
			<ellipse cx={100} cy={136} rx={30} ry={20} fill="#fde7a8" />
			<path d="M90 124 L110 124 L100 134 Z" fill="#8a5a33" />
			<path d="M100 134 Q92 146 84 140 M100 134 Q108 146 116 140" fill="none" stroke="#2b2b3a" strokeWidth={4} strokeLinecap="round" />
			<Cheeks y={128} dx={50} />
		</>
	),
	chick: ({blink}) => (
		<>
			<path d="M92 28 Q96 8 104 26 Q110 10 112 32" fill="none" stroke="#ffc92e" strokeWidth={6} strokeLinecap="round" />
			<ellipse cx={100} cy={110} rx={70} ry={72} fill="#ffe14d" />
			<ellipse cx={36} cy={120} rx={16} ry={28} fill="#ffd23f" transform="rotate(25 36 120)" />
			<ellipse cx={164} cy={120} rx={16} ry={28} fill="#ffd23f" transform="rotate(-25 164 120)" />
			<Eyes y={96} blink={blink} dx={24} />
			<path d="M88 116 L112 116 L100 132 Z" fill="#ff8a1f" strokeLinejoin="round" />
			<Cheeks y={118} dx={44} />
			<path d="M80 180 l-8 14 M80 180 l0 15 M80 180 l8 14 M120 180 l-8 14 M120 180 l0 15 M120 180 l8 14" stroke="#ff8a1f" strokeWidth={5} strokeLinecap="round" />
		</>
	),
	owl: ({blink}) => (
		<>
			<path d="M42 50 L50 14 L76 40 Z M158 50 L150 14 L124 40 Z" fill="#8a5a33" />
			<ellipse cx={100} cy={110} rx={70} ry={80} fill="#a06a3c" />
			<ellipse cx={100} cy={140} rx={42} ry={48} fill="#f3d8b5" />
			{[66, 134].map((x) => (
				<g key={x}>
					<circle cx={x} cy={84} r={28} fill="#fff" />
					<ellipse cx={x} cy={86} rx={13} ry={14 * blink} fill="#2b2b3a" />
					<circle cx={x + 4} cy={80} r={4} fill="#fff" />
				</g>
			))}
			<path d="M92 108 L108 108 L100 124 Z" fill="#ff8a1f" />
			{[120, 140, 160].map((y) => (
				<path key={y} d={`M84 ${y} q8 8 16 0 q8 8 16 0`} fill="none" stroke="#d9b48a" strokeWidth={3} />
			))}
		</>
	),
	zebra: ({blink}) => (
		<>
			<path d="M58 40 L64 4 L84 34 Z M142 40 L136 4 L116 34 Z" fill="#fff" stroke="#2b2b3a" strokeWidth={4} />
			<path d="M80 20 Q100 0 120 20 L116 40 L84 40 Z" fill="#2b2b3a" />
			<ellipse cx={100} cy={100} rx={62} ry={78} fill="#fff" />
			{[54, 76, 98].map((y) => (
				<g key={y} fill="#2b2b3a">
					<path d={`M40 ${y} Q60 ${y - 8} 74 ${y + 4} Q58 ${y + 6} 40 ${y + 12} Z`} />
					<path d={`M160 ${y} Q140 ${y - 8} 126 ${y + 4} Q142 ${y + 6} 160 ${y + 12} Z`} />
				</g>
			))}
			<Eyes y={92} blink={blink} dx={28} />
			<ellipse cx={100} cy={148} rx={44} ry={32} fill="#5b5b6b" />
			<ellipse cx={86} cy={144} rx={6} ry={8} fill="#2b2b3a" />
			<ellipse cx={114} cy={144} rx={6} ry={8} fill="#2b2b3a" />
		</>
	),
	bunny: ({blink}) => (
		<>
			{[72, 128].map((x) => (
				<g key={x} transform={`rotate(${x < 100 ? -8 : 8} ${x} 60)`}>
					<ellipse cx={x} cy={44} rx={19} ry={50} fill="#f4f0f7" />
					<ellipse cx={x} cy={46} rx={9} ry={36} fill="#ffb3c6" />
				</g>
			))}
			<ellipse cx={100} cy={124} rx={72} ry={64} fill="#f4f0f7" />
			<Eyes y={114} blink={blink} dx={28} />
			<path d="M93 134 L107 134 L100 142 Z" fill="#ff7a9c" />
			<path d="M100 142 Q92 152 85 145 M100 142 Q108 152 115 145" fill="none" stroke="#2b2b3a" strokeWidth={4} strokeLinecap="round" />
			<rect x={94} y={147} width={12} height={10} rx={2} fill="#fff" stroke="#d8d0e0" strokeWidth={2} />
			<Cheeks y={136} dx={50} />
		</>
	),
	turtle: ({blink, headOnly}) => (
		<>
			{headOnly ? null : (
				<>
					<ellipse cx={42} cy={170} rx={22} ry={16} fill="#8fd16a" />
					<ellipse cx={158} cy={170} rx={22} ry={16} fill="#8fd16a" />
				</>
			)}
			<ellipse cx={100} cy={92} rx={90} ry={70} fill="#2f8f45" />
			<ellipse cx={100} cy={92} rx={78} ry={58} fill="#46b35a" />
			<path d="M100 44 L128 60 L128 92 L100 108 L72 92 L72 60 Z" fill="#2f8f45" opacity={0.55} />
			<path d="M40 70 L62 62 L72 84 M160 70 L138 62 L128 84" fill="none" stroke="#2f8f45" strokeWidth={6} strokeLinecap="round" opacity={0.55} />
			<ellipse cx={100} cy={136} rx={52} ry={46} fill="#a6e07f" />
			<Eyes y={128} blink={blink} dx={22} />
			<Smile y={150} w={12} />
			<Cheeks y={146} dx={36} />
		</>
	),
	bear: ({blink}) => (
		<>
			<circle cx={46} cy={52} r={28} fill="#9a6235" />
			<circle cx={154} cy={52} r={28} fill="#9a6235" />
			<circle cx={46} cy={52} r={15} fill="#e0a877" />
			<circle cx={154} cy={52} r={15} fill="#e0a877" />
			<ellipse cx={100} cy={112} rx={76} ry={72} fill="#9a6235" />
			<ellipse cx={100} cy={142} rx={38} ry={30} fill="#e0a877" />
			<Eyes y={104} blink={blink} dx={28} />
			<ellipse cx={100} cy={130} rx={14} ry={10} fill="#2b2b3a" />
			<path d="M100 140 L100 148 M100 148 Q91 158 84 151 M100 148 Q109 158 116 151" fill="none" stroke="#2b2b3a" strokeWidth={4} strokeLinecap="round" />
			<Cheeks y={132} dx={56} />
		</>
	),
	pig: ICONS.pig,
	frog: ICONS.frog,
};

// ---------------------------------------------------------------- extra objects (take a color)
const EXTRA: Record<string, React.FC<P>> = {
	balloon: ({color, blink}) => (
		<>
			<path d="M100 160 C 92 175, 110 185, 100 200" stroke="#fff" strokeWidth={3} fill="none" />
			<path d="M100 150 L91 163 L109 163 Z" fill={mix(color, '#000000', 0.2)} />
			<ellipse cx={100} cy={82} rx={62} ry={72} fill={color} />
			<Shine x={72} y={48} />
			<Face x={100} y={88} scale={0.7} blink={blink} />
		</>
	),
	ball: ({color, blink}) => (
		<>
			<circle cx={100} cy={104} r={82} fill={color} />
			<path d="M100 22 Q40 104 100 186 Q160 104 100 22" fill="#fff" opacity={0.85} />
			<path d="M100 22 Q78 104 100 186 Q122 104 100 22" fill={mix(color, '#ffd23f', 0.6)} />
			<Shine x={60} y={62} />
			<Face x={100} y={112} scale={0.62} blink={blink} />
		</>
	),
	gift: ({color, blink}) => (
		<>
			<rect x={30} y={78} width={140} height={108} rx={10} fill={color} />
			<rect x={22} y={60} width={156} height={34} rx={8} fill={mix(color, '#ffffff', 0.2)} />
			<rect x={90} y={60} width={20} height={126} fill="#ffd23f" />
			<path d="M100 60 Q70 20 58 44 Q50 62 100 60 Q150 62 142 44 Q130 20 100 60" fill="#ffd23f" stroke="#e8b400" strokeWidth={3} />
			<Face x={100} y={140} scale={0.6} blink={blink} />
		</>
	),
	cake: ({color, blink}) => (
		<>
			{[70, 100, 130].map((x, i) => (
				<g key={x}>
					<rect x={x - 5} y={24} width={10} height={30} rx={4} fill={['#2f8cff', '#ff6fb5', '#3cc75a'][i]} />
					<path d={`M${x} 6 Q${x + 9} 16 ${x} 24 Q${x - 9} 16 ${x} 6`} fill="#ffb02e" />
				</g>
			))}
			<rect x={26} y={54} width={148} height={130} rx={18} fill="#ffe7c2" />
			<path d="M26 72 Q26 54 44 54 H156 Q174 54 174 72 V96 Q160 110 146 96 Q132 110 118 96 Q104 110 90 96 Q76 110 62 96 Q48 110 34 96 L26 92 Z" fill={color} />
			<Face x={100} y={142} scale={0.62} blink={blink} />
		</>
	),
	banana: ({blink}) => (
		<>
			<path d="M38 52 Q34 160 150 170 Q178 168 170 150 Q90 140 72 46 Q60 34 38 52 Z" fill="#ffd93d" stroke="#e8b400" strokeWidth={4} strokeLinejoin="round" />
			<path d="M40 50 L36 36 L52 40 Z" fill="#7a5230" />
			<Face x={104} y={120} scale={0.55} blink={blink} />
		</>
	),
	strawberry: ({blink}) => (
		<>
			<path d="M100 186 C 40 150, 22 96, 46 66 C 68 42, 132 42, 154 66 C 178 96, 160 150, 100 186 Z" fill="#ff3b4f" />
			{[[66, 90], [100, 80], [134, 90], [80, 130], [120, 130], [100, 160], [58, 112], [142, 112]].map(([x, y]) => (
				<ellipse key={`${x}-${y}`} cx={x} cy={y} rx={3} ry={5} fill="#ffe28a" />
			))}
			<path d="M100 60 L72 40 L92 50 L100 26 L108 50 L128 40 Z" fill="#3cc75a" strokeLinejoin="round" />
			<Face x={100} y={112} scale={0.58} blink={blink} />
		</>
	),
	orange: ({color, blink}) => (
		<>
			<ellipse cx={122} cy={34} rx={22} ry={11} fill="#3cc75a" transform="rotate(-25 122 34)" />
			<circle cx={100} cy={110} r={72} fill={color} />
			{[[70, 80], [130, 90], [90, 150], [140, 140], [60, 130]].map(([x, y], i) => (
				<circle key={i} cx={x} cy={y} r={2.5} fill={mix(color, '#000000', 0.2)} />
			))}
			<Shine x={66} y={78} />
			<Face x={100} y={112} scale={0.7} blink={blink} />
		</>
	),
	cookie: ({color, blink}) => (
		<>
			<circle cx={100} cy={100} r={78} fill={color} />
			{[[60, 60], [140, 70], [55, 130], [145, 135], [100, 165], [100, 40]].map(([x, y], i) => (
				<ellipse key={i} cx={x} cy={y} rx={9} ry={7} fill="#4a2a14" />
			))}
			<Face x={100} y={104} scale={0.75} blink={blink} />
		</>
	),
	egg: ({color, blink}) => (
		<>
			<path d="M100 22 C 150 22, 162 110, 160 130 A60 58 0 0 1 40 130 C 38 110, 50 22, 100 22 Z" fill={color} stroke="#eadfc8" strokeWidth={3} />
			<Shine x={74} y={70} />
			<Face x={100} y={120} scale={0.7} blink={blink} />
		</>
	),
	jellyfish: ({color, blink}) => (
		<>
			{[60, 82, 104, 126, 148].map((x, i) => (
				<path key={x} d={`M${x} 110 q${i % 2 ? 10 : -10} 20 0 40 q${i % 2 ? -10 : 10} 20 0 40`} fill="none" stroke={color} strokeWidth={8} strokeLinecap="round" />
			))}
			<path d="M28 112 C 28 30, 172 30, 172 112 Q150 124 128 112 Q100 126 72 112 Q50 124 28 112 Z" fill={color} />
			<Shine x={66} y={64} />
			<Face x={100} y={86} scale={0.7} blink={blink} />
		</>
	),
	kite: ({color}) => (
		<>
			<path d="M100 120 Q120 150 100 170 Q80 190 104 200" fill="none" stroke="#6b4a1f" strokeWidth={3} />
			{[150, 178].map((y) => (
				<path key={y} d={`M92 ${y} l16 -8 l0 16 Z M108 ${y} l-16 -8`} fill="#ff6fb5" />
			))}
			<path d="M100 8 L160 64 L100 124 L40 64 Z" fill={color} strokeLinejoin="round" />
			<path d="M100 8 L100 124 M40 64 L160 64" stroke={mix(color, '#000000', 0.25)} strokeWidth={4} />
			<path d="M100 8 L160 64 L100 64 Z" fill="#fff" opacity={0.25} />
		</>
	),
	moon: ({color, blink}) => (
		<>
			<path d="M128 18 A86 86 0 1 0 182 140 A70 70 0 1 1 128 18 Z" fill={color} />
			<g transform={`translate(80 104) scale(1 ${blink})`}>
				<path d="M-10 0 Q0 8 10 0" fill="none" stroke="#2b2b3a" strokeWidth={5} strokeLinecap="round" />
			</g>
			<path d="M70 128 Q82 138 94 128" fill="none" stroke="#2b2b3a" strokeWidth={5} strokeLinecap="round" />
			<ellipse cx={62} cy={118} rx={10} ry={6} fill="#ff6f91" opacity={0.45} />
			<path d={starPath(160, 40, 14, 6)} fill="#fff6b0" />
			<path d={starPath(178, 92, 9, 4)} fill="#fff6b0" />
		</>
	),
	nest: ({color}) => (
		<>
			{[70, 100, 130].map((x, i) => (
				<ellipse key={x} cx={x} cy={96 - (i === 1 ? 10 : 0)} rx={22} ry={28} fill="#e9f6ff" stroke="#b8d8ec" strokeWidth={3} />
			))}
			<path d="M20 100 Q100 130 180 100 Q170 170 100 172 Q30 170 20 100 Z" fill={color} />
			{[0, 1, 2, 3].map((i) => (
				<path key={i} d={`M${30 + i * 8} ${112 + i * 14} Q100 ${140 + i * 10} ${170 - i * 8} ${112 + i * 14}`} fill="none" stroke={mix(color, '#000000', 0.3)} strokeWidth={4} />
			))}
		</>
	),
	crown: ({color}) => (
		<>
			<path d="M24 150 L34 56 L72 104 L100 40 L128 104 L166 56 L176 150 Z" fill={color} strokeLinejoin="round" stroke={color} strokeWidth={10} />
			<rect x={24} y={142} width={152} height={26} rx={8} fill={mix(color, '#000000', 0.15)} />
			<circle cx={100} cy={118} r={12} fill="#ff3b3b" />
			<circle cx={58} cy={124} r={9} fill="#2f8cff" />
			<circle cx={142} cy={124} r={9} fill="#3cc75a" />
			{[34, 100, 166].map((x, i) => (
				<circle key={x} cx={x} cy={[56, 40, 56][i]} r={9} fill="#fff6b0" />
			))}
		</>
	),
	rainbow: () => (
		<>
			{['#FF3B3B', '#FF8A1F', '#FFC92E', '#3CC75A', '#2F8CFF', '#9B5CFF'].map((c, i) => (
				<path key={c} d={`M${20 + i * 12} 150 A${80 - i * 12} ${80 - i * 12} 0 0 1 ${180 - i * 12} 150`} fill="none" stroke={c} strokeWidth={13} />
			))}
			{[30, 170].map((x) => (
				<g key={x} fill="#fff">
					<circle cx={x - 14} cy={156} r={16} />
					<circle cx={x + 6} cy={148} r={20} />
					<circle cx={x + 24} cy={158} r={14} />
				</g>
			))}
		</>
	),
	tree: ({color, blink}) => (
		<>
			<rect x={86} y={120} width={28} height={66} rx={8} fill="#8a5a33" />
			<circle cx={100} cy={78} r={60} fill={color} />
			<circle cx={56} cy={104} r={36} fill={color} />
			<circle cx={144} cy={104} r={36} fill={color} />
			<circle cx={70} cy={60} r={6} fill="#ff3b3b" />
			<circle cx={136} cy={74} r={6} fill="#ff3b3b" />
			<Face x={100} y={96} scale={0.65} blink={blink} />
		</>
	),
	umbrella: ({color}) => (
		<>
			<path d="M100 96 L100 168 Q100 186 116 186 Q130 186 130 172" fill="none" stroke="#6b4a1f" strokeWidth={8} strokeLinecap="round" />
			<path d="M16 100 A84 80 0 0 1 184 100 Q170 86 156 100 Q142 86 128 100 Q114 86 100 100 Q86 86 72 100 Q58 86 44 100 Q30 86 16 100 Z" fill={color} />
			<path d="M100 20 Q70 50 72 100 M100 20 Q130 50 128 100" fill="none" stroke={mix(color, '#000000', 0.2)} strokeWidth={4} />
			<circle cx={100} cy={16} r={6} fill={mix(color, '#000000', 0.2)} />
		</>
	),
	van: ({color, blink}) => (
		<>
			<path d="M14 150 L14 70 Q14 50 34 50 L140 50 Q160 50 172 80 L186 112 L186 150 Z" fill={color} />
			<path d="M118 62 L144 62 Q154 62 160 80 L168 100 L118 100 Z" fill="#d6f1ff" />
			<rect x={30} y={62} width={74} height={38} rx={8} fill="#d6f1ff" />
			<Face x={67} y={128} scale={0.45} blink={blink} />
			{[52, 148].map((x) => (
				<g key={x}>
					<circle cx={x} cy={154} r={22} fill="#2b2b3a" />
					<circle cx={x} cy={154} r={9} fill="#cfcfd8" />
				</g>
			))}
		</>
	),
	watermelon: ({blink}) => (
		<>
			<path d="M16 80 A84 84 0 0 0 184 80 Z" fill="#3cc75a" />
			<path d="M28 80 A72 72 0 0 0 172 80 Z" fill="#fff" />
			<path d="M36 80 A64 64 0 0 0 164 80 Z" fill="#ff4f6a" />
			{[[70, 100], [100, 120], [130, 100], [86, 128], [116, 128]].map(([x, y], i) => (
				<ellipse key={i} cx={x} cy={y} rx={4} ry={7} fill="#2b2b3a" />
			))}
			<Face x={100} y={96} scale={0.45} blink={blink} />
		</>
	),
	xylophone: () => (
		<>
			{['#FF3B3B', '#FF8A1F', '#FFC92E', '#3CC75A', '#2F8CFF', '#9B5CFF'].map((c, i) => (
				<rect key={c} x={22 + i * 27} y={50 + i * 8} width={22} height={120 - i * 16} rx={6} fill={c} />
			))}
			<path d="M20 70 L190 100 M20 150 L190 130" stroke="#8a5a33" strokeWidth={6} strokeLinecap="round" />
			<path d="M150 20 L110 70" stroke="#8a5a33" strokeWidth={6} strokeLinecap="round" />
			<circle cx={150} cy={20} r={10} fill="#ff6fb5" />
		</>
	),
	yoyo: ({color, blink}) => (
		<>
			<path d="M100 10 L100 46" stroke="#6b6b7b" strokeWidth={3} />
			<circle cx={100} cy={120} r={74} fill={color} />
			<circle cx={100} cy={120} r={50} fill={mix(color, '#ffffff', 0.35)} />
			<Shine x={66} y={86} />
			<Face x={100} y={122} scale={0.65} blink={blink} />
		</>
	),
};

export const ALL_ICONS: Record<string, React.FC<P>> = {...ICONS, ...EXTRA, ...ANIMALS};

export const Icon: React.FC<{name: string; color: string; size: number; blink: number}> = ({name, color, size, blink}) => {
	const Comp = ALL_ICONS[name];
	return (
		<svg width={size} height={size} viewBox="0 0 200 200" style={{overflow: 'visible'}}>
			<Comp color={color} blink={blink} />
		</svg>
	);
};

// ---------------------------------------------------------------- shapes with faces
const SHAPES: Record<string, (c: string) => React.ReactNode> = {
	circle: (c) => <circle cx={100} cy={100} r={84} fill={c} />,
	square: (c) => <rect x={22} y={22} width={156} height={156} rx={14} fill={c} />,
	triangle: (c) => <path d="M100 24 L182 168 L18 168 Z" fill={c} stroke={c} strokeWidth={16} strokeLinejoin="round" />,
	rectangle: (c) => <rect x={6} y={50} width={188} height={110} rx={12} fill={c} />,
	star: (c) => <path d={starPath(100, 108, 92, 42)} fill={c} stroke={c} strokeWidth={14} strokeLinejoin="round" />,
	heart: (c) => (
		<path d="M100 182 C 38 134, 6 98, 26 58 C 46 20, 90 30, 100 62 C 110 30, 154 20, 174 58 C 194 98, 162 134, 100 182 Z" fill={c} />
	),
	oval: (c) => <ellipse cx={100} cy={100} rx={94} ry={66} fill={c} />,
	diamond: (c) => <path d="M100 10 L176 100 L100 190 L24 100 Z" fill={c} stroke={c} strokeWidth={12} strokeLinejoin="round" />,
};
const SHAPE_FACE_Y: Record<string, number> = {triangle: 122, star: 116, heart: 100, rectangle: 108};

export const ShapeFace: React.FC<{shape: string; color: string; size: number; blink: number; face?: boolean}> = ({
	shape,
	color,
	size,
	blink,
	face = true,
}) => (
	<svg width={size} height={size} viewBox="0 0 200 200" style={{overflow: 'visible'}}>
		{SHAPES[shape](color)}
		{face ? <Face x={100} y={SHAPE_FACE_Y[shape] ?? 102} scale={shape === 'triangle' || shape === 'star' ? 0.6 : 0.8} blink={blink} /> : null}
	</svg>
);
