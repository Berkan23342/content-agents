import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {Episode, EpisodeProps, EpisodeThumbnail} from './Episode';
import {Logo} from './Brand';
import {Short, ShortProps} from './Short';
import {StoryShort, StoryShortProps} from './StoryShort';

// Real props come from build/<date>/props.json via `--props`; this is only a Studio placeholder.
const placeholder: EpisodeProps = {
	durationInFrames: 150,
	audio: '',
	scenes: [{type: 'intro', from: 0, duration: 150, title: ['Learn Colors', '& Numbers!'], heroes: []}],
	thumb: {title: ['Learn Colors', '& Numbers!'], heroes: []},
};

const shortPlaceholder: ShortProps = {durationInFrames: 150, audio: '', bg: 'day', header: 'Guess the Shadow', scenes: []};
const storyShortPlaceholder: StoryShortProps = {
	durationInFrames: 150,
	audio: '',
	title: 'A Story',
	scenes: [{type: 'story', from: 0, duration: 150, bg: 'park', actors: [], props: [], bubbles: [], title: null, cam: []}],
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
		<Composition
			id="Short"
			component={Short}
			defaultProps={shortPlaceholder}
			calculateMetadata={({props}) => ({durationInFrames: props.durationInFrames})}
			durationInFrames={150}
			fps={30}
			width={1080}
			height={1920}
		/>
		<Composition
			id="StoryShort"
			component={StoryShort}
			defaultProps={storyShortPlaceholder}
			calculateMetadata={({props}) => ({durationInFrames: props.durationInFrames})}
			durationInFrames={150}
			fps={30}
			width={1080}
			height={1920}
		/>
		<Composition id="Thumbnail" component={EpisodeThumbnail} defaultProps={placeholder} durationInFrames={1} fps={30} width={1920} height={1080} />
		<Composition id="Logo" component={Logo} durationInFrames={1} fps={30} width={800} height={800} />
	</>
);

registerRoot(Root);
