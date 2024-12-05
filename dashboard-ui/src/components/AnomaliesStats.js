import React, { useEffect, useState } from 'react';
import '../App.css';

export default function AnomaliesStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [latestAnomaly, setLatestAnomaly] = useState(null);
    const [error, setError] = useState(null);

    const getAnomalies = () => {
        fetch(`http://kafka-group35.westus.cloudapp.azure.com/anomalies/anomalies`)
            .then(res => res.json())
            .then((result) => {
                console.log("Received Anomalies");
                console.log(result);
                if (result.length > 0) {
                    setLatestAnomaly(result[result.length - 1]); // Set the latest anomaly
                }
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
    } else if (latestAnomaly) {
        return (
            <div>
                <h1>Latest Anomaly</h1>
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
                        <tr>
                            <td>{latestAnomaly.event_id}</td>
                            <td>{latestAnomaly.trace_id}</td>
                            <td>{latestAnomaly.event_type}</td>
                            <td>{latestAnomaly.anomaly_type}</td>
                            <td>{latestAnomaly.description}</td>
                            <td>{latestAnomaly.timestamp}</td>
                        </tr>
                    </tbody>
                </table>
                <h3>Last Updated: {new Date().toLocaleString()}</h3>
            </div>
        );
    } else {
        return (<div>No anomalies detected.</div>);
    }
}