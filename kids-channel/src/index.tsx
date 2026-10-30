import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {Episode, EpisodeProps, EpisodeThumbnail} from './Episode';
import {Logo} from './Brand';

// Real props come from build/<date>/props.json via `--props`; this is only a Studio placeholder.
const placeholder: EpisodeProps = {
	durationInFrames: 150,
	audio: '',
	scenes: [{type: 'intro', from: 0, duration: 150, title: ['Learn Colors', '& Numbers!'], heroes: []}],
	thumb: {title: ['Learn Colors', '& Numbers!'], heroes: []},
};

const Root: React.FC = () => (
	<>
		<Composition
			id="Episode"
			component={Episode}
			defaultProps={placeholder}
			calculateMetadata={({props}) => ({durationInFrames: props.durationInFrames})}
			durationInFrames={150}
			fps={30}
			width={1920}
			height={1080}
		/>
		<Composition id="Thumbnail" component={EpisodeThumbnail} defaultProps={placeholder} durationInFrames={1} fps={30} width={1920} height={1080} />
		<Composition id="Logo" component={Logo} durationInFrames={1} fps={30} width={800} height={800} />
	</>
);

registerRoot(Root);
