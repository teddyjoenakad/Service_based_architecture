import logo from './logo.png';
import './App.css';

import EndpointAnalyzer from './components/EndpointAnalyzer';
import AppStats from './components/AppStats';
import AnomaliesStats from './components/AnomaliesStats'; // Import AnomaliesStats

function App() {

    const endpoints = ["parking", "payment"];

    const rendered_endpoints = endpoints.map((endpoint) => {
        return <EndpointAnalyzer key={endpoint} endpoint={endpoint} />;
    });

    return (
        <div className="App">
            <img src={logo} className="App-logo" alt="logo" height="150px" width="150px" />
            <div>
                <AppStats />
                <AnomaliesStats />
                <h1>Analyzer Endpoints</h1>
                {rendered_endpoints}
            </div>
        </div>
    );

}

export default App;