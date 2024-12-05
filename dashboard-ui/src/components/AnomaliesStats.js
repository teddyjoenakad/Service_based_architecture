import React, { useEffect, useState } from 'react';
import '../App.css';

export default function AnomaliesStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [anomalies, setAnomalies] = useState([]);
    const [error, setError] = useState(null);

    const getAnomalies = () => {
        fetch(`http://kafka-group35.westus.cloudapp.azure.com/anomalies/anomalies`)
            .then(res => res.json())
            .then((result) => {
                console.log("Received Anomalies");
                console.log(result);
                setAnomalies(result);
                setIsLoaded(true);
            }, (error) => {
                setError(error);
                setIsLoaded(true);
            });
    };

    useEffect(() => {
        const interval = setInterval(() => getAnomalies(), 2000); // Update every 2 seconds
        return () => clearInterval(interval);
    }, []);

    if (error) {
        return (<div className={"error"}>Error found when fetching from API</div>);
    } else if (isLoaded === false) {
        return (<div>Loading...</div>);
    } else {
        return (
            <div>
                <h1>Latest Anomalies</h1>
                <table className={"StatsTable"}>
                    <tbody>
                        <tr>
                            <th>Event ID</th>
                            <th>Trace ID</th>
                            <th>Event Type</th>
                            <th>Anomaly Type</th>
                            <th>Description</th>
                            <th>Timestamp</th>
                        </tr>
                        {anomalies.map(anomaly => (
                            <tr key={anomaly.event_id}>
                                <td>{anomaly.event_id}</td>
                                <td>{anomaly.trace_id}</td>
                                <td>{anomaly.event_type}</td>
                                <td>{anomaly.anomaly_type}</td>
                                <td>{anomaly.description}</td>
                                <td>{anomaly.timestamp}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                <h3>Last Updated: {new Date().toLocaleString()}</h3>
            </div>
        );
    }
}