import React, { useEffect, useState } from 'react';
import '../App.css';

export default function AnomaliesStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [latestParkingAnomaly, setLatestParkingAnomaly] = useState(null);
    const [latestPaymentAnomaly, setLatestPaymentAnomaly] = useState(null);
    const [error, setError] = useState(null);

    const getAnomalies = () => {
        fetch(`http://kafka-acit3855.westus.cloudapp.azure.com/anomalies/anomalies`)
            .then(res => res.json())
            .then((result) => {
                console.log("Received Anomalies");
                console.log(result);
                const latestParking = result.filter(anomaly => anomaly.event_type === "parking_status").pop();
                const latestPayment = result.filter(anomaly => anomaly.event_type === "payment").pop();
                setLatestParkingAnomaly(latestParking);
                setLatestPaymentAnomaly(latestPayment);
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
                        {latestParkingAnomaly && (
                            <tr>
                                <td>{latestParkingAnomaly.event_id}</td>
                                <td>{latestParkingAnomaly.trace_id}</td>
                                <td>{latestParkingAnomaly.event_type}</td>
                                <td>{latestParkingAnomaly.anomaly_type}</td>
                                <td>{latestParkingAnomaly.description}</td>
                                <td>{latestParkingAnomaly.timestamp}</td>
                            </tr>
                        )}
                        {latestPaymentAnomaly && (
                            <tr>
                                <td>{latestPaymentAnomaly.event_id}</td>
                                <td>{latestPaymentAnomaly.trace_id}</td>
                                <td>{latestPaymentAnomaly.event_type}</td>
                                <td>{latestPaymentAnomaly.anomaly_type}</td>
                                <td>{latestPaymentAnomaly.description}</td>
                                <td>{latestPaymentAnomaly.timestamp}</td>
                            </tr>
                        )}
                    </tbody>
                </table>
                <h3>Last Updated: {new Date().toLocaleString()}</h3>
            </div>
        );
    }
}